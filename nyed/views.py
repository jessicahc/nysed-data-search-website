from io import BytesIO
import base64
from django.http import HttpResponse
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.stats import pearsonr, spearmanr
from .models import  BEDS_Mapping, ELA_Result, Math_Result, Correlation_Data

SUBJECT_ELA = 1
SUBJECT_MATH = 2

# Pre-load all beds_code mappings for search form's autocomplete feature
def get_beds_mapping_list():
    #TODO: need to filter out any mappings that should not be in the autocomplete list?
    return BEDS_Mapping.objects.all()

def home(request):
    return render(request, 'nyed/home.html')

def about(request):
    return render(request, 'nyed/about.html')

def base_assessment(request):
    context = {
        'beds_mapping_list': get_beds_mapping_list() #For search form's autocomplete feature
    }
    return render(request, 'nyed/base_assessment.html', context)


# Go back to the basic assessment data search page with error msg displayed
# as a result of a previous search
def goback_base_assessment(request, error_msg):
    context = {
        'error_msg': error_msg,
        'beds_mapping_list': get_beds_mapping_list() #For search form's autocomplete feature
    }
    return render(request, 'nyed/base_assessment.html', context)


def assessment_data(request):
    
    if (request is None or request.GET is None or
        not all (key in request.GET for key in ('entity_name','entity_bedscode', 'year', 'grade'))):
        print("Invoked assessment_data: request.GET not received or keys in request.GET missing")
        return base_assessment(request)
    else:
        print(request.GET)

    req_beds_code = request.GET['entity_bedscode']

    if (req_beds_code == None or req_beds_code == ''):
        error = 'Input Error: Missing or invalic District/School Name. Please enter a valid district or school name and try again.'
        print(error)
        return goback_base_assessment(request, error)

    req_entity_name = request.GET['entity_name']
    req_year = int(request.GET['year'])
    req_grade = int(request.GET['grade'])

    # Retrieve district name from nyed_beds_mapping table
    district_info = BEDS_Mapping.objects.get(beds_code=req_beds_code)

    # Get G3-G8 ELA or Math assessment data from DB and generate corresponding charts
    (ela_resultset_dict, ela_chart) = get_assessment_chart(SUBJECT_ELA, req_beds_code, req_year, req_grade)
    (math_resultset_dict, math_chart) = get_assessment_chart(SUBJECT_MATH, req_beds_code, req_year, req_grade)

    context = {
       'beds_mapping_list': get_beds_mapping_list(), #For search form's autocomplete feature
       'district_info': district_info,
       'req_entity_name': req_entity_name,
       'req_beds_code': req_beds_code,
       'req_year': req_year,
       'req_grade': req_grade,
       'req_school_year': '{}-{}'.format(req_year-1, req_year),
       'ela_result_dict': ela_resultset_dict,
       'ela_chart':ela_chart,
       'math_result_dict': math_resultset_dict,
       'math_chart':math_chart
    }
    return render(request, 'nyed/assessment_content.html', context)

# Retrieve G3-G8 ELA or Math assessment data from DB and create charts based on student count
def get_assessment_chart(subject, bedscode, year, grade):
    resultset_dict = {
        'year_grade': [],
        'L1_count': [],
        'L1_pct': [],
        'L2_count': [],
        'L2_pct': [],
        'L3_count': [],
        'L3_pct': [],
        'L4_count': [],
        'L4_pct': [],
        'total_tested': [],
        'avg_rawscore': []
    }
    subject_data = None

    year_gap = grade - 3
    start_year = year - year_gap
    start_grade = 3

    # No data is currently available before 2013, start from 2013 and adjust grade level
    if (start_year < 2013):
        adjusted_years = 2013 - start_year
        start_year = 2013
        start_grade = 3 + adjusted_years

    for i in range(6):
        query_year = start_year + i
        query_grade = start_grade + i
        if (query_grade > 8):
            break

        try:
            if subject == SUBJECT_ELA:
                subject_data = ELA_Result.objects.get(beds_code_id=bedscode, year=query_year, grade=query_grade)
            elif subject == SUBJECT_MATH:
                subject_data = Math_Result.objects.get(beds_code_id=bedscode, year=query_year, grade=query_grade)

            if subject_data != None:
                resultset_dict['year_grade'].append('{}\nG{}'.format(query_year, query_grade))
                resultset_dict['L1_count'].append(subject_data.L1_count)
                resultset_dict['L1_pct'].append(subject_data.L1_percent)
                resultset_dict['L2_count'].append(subject_data.L2_count)
                resultset_dict['L2_pct'].append(subject_data.L2_percent)
                resultset_dict['L3_count'].append(subject_data.L3_count)
                resultset_dict['L3_pct'].append(subject_data.L3_percent)
                resultset_dict['L4_count'].append(subject_data.L4_count)
                resultset_dict['L4_pct'].append(subject_data.L4_percent)
                resultset_dict['total_tested'].append(subject_data.total_tested)
                resultset_dict['avg_rawscore'].append(subject_data.mean_score)

        except ObjectDoesNotExist:
            error = 'DNE Error: Cannot find District/School \"{}\" & Year {} & Grade{}.'.format(bedscode, query_year, query_grade)
            print(error)

    title = '{}-Grade{} Student Group\n{} Assessment History\n'.format(year, grade,
                                                                    'ELA' if subject == SUBJECT_ELA else 'Math')
    chart = gen_studentcount_barchart(title, resultset_dict)
    return (resultset_dict, chart)

# Generate stacked bar chart based on the student count of the assessment data
def gen_studentcount_barchart(title, result_dict):
    xlabels = result_dict['year_grade']
    L1_list = result_dict['L1_count']
    L2_list = result_dict['L2_count']
    L3_list = result_dict['L3_count']
    L4_list = result_dict['L4_count']
    subplots_ratio = [3,1]
    num_bars = len(xlabels)

    # Some schools don't have complete data. To prevent bars looking too fat,
    # pad extra empty data if less than 3 bars will be drawn
    if (num_bars < 3):
        # Make copy of the lists so they won't affect the orig data to be displayed in html tables
        xlabels = result_dict['year_grade'].copy()
        L1_list = result_dict['L1_count'].copy()
        L2_list = result_dict['L2_count'].copy()
        L3_list = result_dict['L3_count'].copy()
        L4_list = result_dict['L4_count'].copy()
        for i in range(num_bars, 3):
            xlabels.append('')
            L1_list.append(0)
            L2_list.append(0)
            L3_list.append(0)
            L4_list.append(0)
        num_bars = len(xlabels) # update number of bars including empty ones
        subplots_ratio = [2,1]

    plt.switch_backend('AGG')
    plt.rcParams['font.sans-serif'] = ['Verdana', 'Arial', 'Tahoma', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['font.size'] = 9.5
    plt.rcParams["savefig.dpi"] = 100
    plt.title('\n', loc='center', fontsize=6) # Make extra space on top of the figure

    # Cannot fit the legend nicely around the bar chart - always overlapped with the bars.
    # So workaround this problem by creating 2 subplots: 1 subplot for graph &
    # 1 subplot for legend in 3:1 or 2:1 ratio to display legend outside of the graph
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 3.5), gridspec_kw={'width_ratios': subplots_ratio})

    xticks = list(range(num_bars))
    ax1.set_xticks(xticks)
    ax1.tick_params(axis='both', color='w') # Hide tick lines
    ax1.set_xticklabels(xlabels)
    barwidth = 0.5
    ax1.bar(xticks, L1_list, barwidth, color=(1,0.57,0,0.7))
    ax1.bar(xticks, L2_list, barwidth, bottom=L1_list, color=(1,0.9,0.43,0.8)) #color='ffe66d'
    cum_list = np.add(L1_list, L2_list)
    ax1.bar(xticks, L3_list, barwidth, bottom=cum_list, color=(0.56,0.79,0.9,0.7)) #color='8ecae6'
    cum_list = np.add(cum_list, L3_list)
    ax1.bar(xticks, L4_list, barwidth, bottom=cum_list, color=(0.13,0.62,0.74,0.7)) #color='219ebc'

    ax1.set_xlabel('Year & Grade Level')
    ax1.set_ylabel('\n# of Students Scored 1-4')
    ax1.yaxis.grid(color='gray', linestyle='dashed', linewidth=0.5, alpha=0.5)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Use 2nd subplot space to display legend
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.set_yticks([])
    ax2.set_xticks([])
    legend_labels = ['Score 1\n(Not Proficient)', 'Score 2\n(Partially Proficient)  ',
                     'Score 3\n(Proficient)', 'Score 4\n(Advanced)']
    fig.legend(legend_labels, loc='center right', ncol=1, frameon=False, fontsize=9,
                borderaxespad=0.1, handletextpad=0.5, handlelength=1)
    plt.subplots_adjust(hspace=0, wspace=0.1)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph


def base_correlation(request):
    return render(request, 'nyed/base_correlation.html', {})


def correlation_data(request):
    if (request is None or request.GET is None or
        not all (key in request.GET for key in ('correlation_type', 'year'))):
        print("Invoked correlation_data: request.GET not received or keys in request.GET missing")
        return base_correlation(request)
    else:
        print(request.GET)

    req_corr_type = request.GET['correlation_type']
    req_year = int(request.GET['year'])

    corr_context = None

    # Get G3-G8 ELA or Math assessment data from DB and generate corresponding charts
    if (req_corr_type == 'ACS'):
        corr_context, error = get_classsize_scatterplot(req_year, request.GET['year'])
    elif (req_corr_type == 'PFL'):
        corr_context, error = get_freelunch_scatterplot(req_year, request.GET['year'])

    if (corr_context == None):
        corr_context = {}

    if (error != None):
        corr_context['error_msg'] = error
    corr_context['req_corr_type'] = req_corr_type
    corr_context['req_year'] = req_year

    return render(request, 'nyed/correlation_content.html', corr_context)


# Create correlation scatterplot for ELA/Math asessement results vs. Avg Class Size
def get_classsize_scatterplot(year, year_str):
    class_size = []
    ela_L1_pct= []
    math_L1_pct= []
    error = None

    try:
        classsize_data = Correlation_Data.objects.filter(beds_code_id__beds_code__iendswith='0000', year=year).values('g1to6_class_size', 'ela_g3to6_L1_percent', 'math_g3to6_L1_percent')

        if classsize_data != None:
            for row in classsize_data:
                class_size.append(row["g1to6_class_size"])
                ela_L1_pct.append(row["ela_g3to6_L1_percent"])
                math_L1_pct.append(row["math_g3to6_L1_percent"])

    except ObjectDoesNotExist:
        error = 'DoesNotExist Error: Cannot retrieve avg_class_size data for year ' + year_str
        print(error)
        return (None, error)

    xlabel = 'Average Class Size'
    ylabel = '% of Students Scored 1 (Not Proficient)'

    # ELA
    ela_title = year_str + ' ELA Assessment Results vs. Average Class Size\n\n(based on State-wide Per-district Data)'
    ela_scatterplot = gen_scatterplot(ela_title, xlabel, class_size, ylabel, ela_L1_pct)

    #calculate R-value - use Pearson's R-value for now
    ela_p_corr, pval = pearsonr(class_size, ela_L1_pct)
    #ela_s_corr, sval = spearmanr(class_size, ela_L1_pct)
    #print('ELA Spearman correlation: %.3f' % ela_s_corr)
    ela_corr_strength = 'There is ' + get_corr_strength(ela_p_corr) + ' correlation between Students\' ELA Non-Proficiency and Average Class Size'

    # Math
    math_title = year_str + ' Math Assessment Results vs. Average Class Size\n\n(based on State-wide Per-district Data)'
    math_scatterplot = gen_scatterplot(math_title, xlabel, class_size, ylabel, math_L1_pct)

    #calculate R-value - use Pearson's R-value for now
    math_p_corr, pval = pearsonr(class_size, math_L1_pct)
    #math_s_corr, sval = spearmanr(class_size, math_L1_pct)
    #print('Math Spearman correlation: %.3f' % math_s_corr)
    math_corr_strength = 'There is ' + get_corr_strength(math_p_corr) + ' correlation between Students\' Math Non-Proficiency and Average Class Size'

    context = {
       'ela_scatter_plot': ela_scatterplot,
       'ela_pearsons_rval': '%.3f' % ela_p_corr,
       'ela_corr_strength' : ela_corr_strength,
       'math_scatter_plot': math_scatterplot,
       'math_pearsons_rval': '%.3f' % math_p_corr,
       'math_corr_strength' : math_corr_strength,
    }
    return (context, error)

# Create correlation scatterplot for ELA/Math asessement results vs. Avg Class Size
def get_freelunch_scatterplot(year, year_str):
    ela_L1_pct = []
    math_L1_pct = []
    freelunch = []
    error = None

    try:
        freelunch_data = Correlation_Data.objects.filter(beds_code_id__beds_code__iendswith='0000', year=year).values('ela_g3to6_L1_percent', 'math_g3to6_L1_percent', 'per_free_lunch')

        if freelunch_data != None:
            for row in freelunch_data:
                ela_L1_pct.append(row["ela_g3to6_L1_percent"])
                math_L1_pct.append(row["math_g3to6_L1_percent"])
                freelunch.append(row["per_free_lunch"])

    except ObjectDoesNotExist:
        error = 'DoesNotExist Error: Cannot retrieve pct_free_lunch data for year ' + year_str
        print(error)
        return (None, error)

    xlabel = '% of Students Eligible for Free Lunch'
    ylabel = '% of Students Scored 1 (Not Proficient)'

    # ELA
    ela_title = year_str + ' ELA Assessment Results vs. Free Lunch Eligibility\n\n(based on State-wide Per-district Data)'
    ela_scatterplot = gen_scatterplot(ela_title, xlabel, freelunch, ylabel, ela_L1_pct)

    # Calculate R-values
    ela_p_corr, pval = pearsonr(freelunch, ela_L1_pct)
    ela_s_corr, sval = spearmanr(freelunch, ela_L1_pct)
    print('ELA Spearman correlation: %.3f' % ela_s_corr)
    ela_corr_strength = 'There is ' + get_corr_strength(ela_p_corr) + ' correlation between Students\' ELA Non-Proficiency and Free Lunch Eligibility'

    # Math
    math_title = year_str + ' Math Assessment Results vs. Free Lunch Eligibility\n\n(Based on State-wide Per-district Data)'
    math_scatterplot = gen_scatterplot(math_title, xlabel, freelunch, ylabel, math_L1_pct)

    # Calculate R-values
    math_p_corr, pval = pearsonr(freelunch, math_L1_pct)
    print('Math Pearsons correlation: %.3f' % math_p_corr)
    math_s_corr, sval = spearmanr(freelunch, math_L1_pct)
    print('Math Spearman correlation: %.3f' % math_s_corr)
    math_corr_strength = 'There is ' + get_corr_strength(ela_p_corr) + ' correlation between Students\' Math Non-Proficiency and Free Lunch Eligibility'

    context = {
       'ela_scatter_plot': ela_scatterplot,
       'ela_pearsons_rval': '%.3f' % ela_p_corr,
       'ela_corr_strength' : ela_corr_strength,
       'math_scatter_plot': math_scatterplot,
       'math_pearsons_rval': '%.3f' % math_p_corr,
       'math_corr_strength' : math_corr_strength,
    }
    return (context, error)


def gen_scatterplot(title, xlabel, xlist_data, ylabel, ylist_data):
    plt.switch_backend('AGG')
    plt.rcParams['font.sans-serif'] = ['Verdana', 'Arial', 'Tahoma', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['font.size'] = 8.5
    plt.rcParams["savefig.dpi"] = 100

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(xlist_data, ylist_data)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph


def get_corr_strength(r):
    if (r >= -1 and r <= -0.5):
        return 'STRONG (negative)'
    elif (r > -0.5 and r <= -0.3):
        return 'MODERATE (negative)'
    elif (r > -0.3 and r <= -0.1):
        return 'WEAK (negative)'
    elif (r > -0.1 and r < 0.1):
        return ('VERY WEAK')
    elif (r >= 0.1 and r < 0.3):
        return 'WEAK (positive)'
    elif (r >= 0.3 and r < 0.5):
        return 'MODERATE (positive)'
    elif (r >= 0.5 and r <= 1):
        return 'STRONG (positive)'


######### THE FOLLOWING CODE IS NO LONGER USED! #############
# Retrieve G3-G8 ELA or Math assessment data from DB and create charts based on percentage data
def get_resultset_pctchart(subject, bedscode, year, grade):
    year_gap = grade - 3
    start_year = year - year_gap
    result_list = []
    L1_pct_list = []
    L2_pct_list = []
    L3_pct_list = []
    L4_pct_list = []
    year_grade_list = []
    subject_data = None

    for i in range(6):
        query_year = start_year+i
        query_grade = 3+i

        try:
            if subject == SUBJECT_ELA:
                subject_data = ELA_Result.objects.get(beds_code_id=bedscode, year=query_year, grade=query_grade)
            elif subject == SUBJECT_MATH:
                subject_data = Math_Result.objects.get(beds_code_id=bedscode, year=query_year, grade=query_grade)

            if subject_data != None:
                result_list.append(subject_data)
                L1_pct_list.append(subject_data.L1_percent)
                L2_pct_list.append(subject_data.L2_percent)
                L3_pct_list.append(subject_data.L3_percent)
                L4_pct_list.append(subject_data.L4_percent)
                year_grade_list.append('{}\nG{}'.format(query_year, query_grade))
        except ObjectDoesNotExist:
            print('DoesNotExist error for year{}, grade{}'.format(query_year, query_grade))

    print(result_list)
    print(L1_pct_list)
    print(L2_pct_list)
    print(L3_pct_list)
    print(L4_pct_list)
    print(year_grade_list)

    title = '{}-Grade{} Student Group\n{} Assessment History\n'.format(year, grade,
                                                                    'ELA' if subject == SUBJECT_ELA else 'Math')
    chart = gen_bar_chart(title, year_grade_list,
                          L1_pct_list, L2_pct_list, L3_pct_list, L4_pct_list)
    return (result_list, chart)


def gen_percent_barchart(title, xlabels, L1_list, L2_list, L3_list, L4_list):

    plt.switch_backend('AGG')
    plt.rcParams['font.sans-serif'] = ['Verdana', 'Arial', 'Tahoma', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['font.size'] = 8.5
    print("dpi")
    plt.rcParams["savefig.dpi"] = 100

    fig, ax = plt.subplots(figsize=(4.5, 3.5))

    width = 0.5
    ax.bar(xlabels, L1_list, width, color=(1,0.57,0,0.7))
    ax.bar(xlabels, L2_list, width, bottom=L1_list, color=(1,0.9,0.43,0.8)) #color='ffe66d'
    cum_list = np.add(L1_list, L2_list)
    ax.bar(xlabels, L3_list, width, bottom=cum_list, color=(0.56,0.79,0.9,0.7)) #color='8ecae6'
    cum_list = np.add(cum_list, L3_list)
    ax.bar(xlabels, L4_list, width, bottom=cum_list, color=(0.13,0.62,0.74,0.7)) #color='219ebc'

    # Display y-axis labels with %, add an extra tick to create gap for legend
    pct_ticks = [0,20,40,60,80,100,122]
    pct_labels = ['0%', '20%', '40%', '60%', '80%', '100%', '']
    plt.yticks(pct_ticks, pct_labels)

    ax.set_xlabel('Year - Grade Level')
    ax.set_ylabel('% of Students Received Score 1-4')
    ax.set_title(title, loc='center', fontsize=10)

    ax.yaxis.grid(color='gray', linestyle='dashed', linewidth=0.5, alpha=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    legend_labels = ['Score 1 (Below Expected)', 'Score 2 (Partially Proficient)',
                     'Score 3 (Proficient)', 'Score 4 (Excellent)']
    leg = plt.legend(legend_labels, loc='upper center', ncol=2, frameon=False, fontsize=8,
                     labelspacing=0.25, columnspacing=0.5, borderaxespad=0, handletextpad=0.5, handlelength=1)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph