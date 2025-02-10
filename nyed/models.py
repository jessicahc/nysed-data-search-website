from django.db import models

# Create your models here.

class BEDS_Mapping(models.Model):
    beds_code = models.CharField(max_length=15, primary_key=True)
    name_desc = models.CharField(max_length=200)
    nrc_code = models.SmallIntegerField(null=True)

    def __str__(self):
        return self.beds_code + '\t' + self.name_desc



class ELA_Result(models.Model):
    beds_code = models.ForeignKey('BEDS_Mapping', on_delete=models.CASCADE)
    year = models.SmallIntegerField()
    grade = models.SmallIntegerField()
    total_tested = models.IntegerField()
    L1_count = models.IntegerField()
    L1_percent = models.SmallIntegerField()
    L2_count = models.IntegerField()
    L2_percent = models.SmallIntegerField()
    L3_count = models.IntegerField()
    L3_percent = models.SmallIntegerField()
    L4_count = models.IntegerField()
    L4_percent = models.SmallIntegerField()
    mean_score = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['beds_code', 'year', 'grade']),
        ]

    def __str__(self):
        return '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(self.beds_code, self.year, self.grade, self.total_tested, 
                                                       self.L1_percent, self.L2_percent, self.L3_percent, self.L4_percent) 


class Math_Result(models.Model):
    beds_code = models.ForeignKey('BEDS_Mapping', on_delete=models.CASCADE)
    year = models.SmallIntegerField()
    grade = models.SmallIntegerField()
    total_tested = models.IntegerField()
    L1_count = models.IntegerField()
    L1_percent = models.SmallIntegerField()
    L2_count = models.IntegerField()
    L2_percent = models.SmallIntegerField()
    L3_count = models.IntegerField()
    L3_percent = models.SmallIntegerField()
    L4_count = models.IntegerField()
    L4_percent = models.SmallIntegerField()
    mean_score = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['beds_code', 'year', 'grade']),
        ]

    def __str__(self):
        return '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(self.beds_code, self.year, self.grade, self.total_tested, 
                                                       self.L1_percent, self.L2_percent, self.L3_percent, self.L4_percent) 

class Correlation_Data(models.Model):
    beds_code = models.ForeignKey('BEDS_Mapping', on_delete=models.CASCADE)
    year = models.SmallIntegerField()
    ela_g3to6_L1_percent = models.SmallIntegerField(null=True, blank=True)
    math_g3to6_L1_percent = models.SmallIntegerField(null=True, blank=True)
    g1to6_class_size = models.SmallIntegerField()
    per_free_lunch = models.SmallIntegerField(null=True, blank=True)
    per_reduced_lunch = models.SmallIntegerField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['beds_code', 'year']),
        ]

    def __str__(self):
        return '{}\t{}\t{}\t{}\t{}\n'.format(self.beds_code, self.year, 
                                        self.ela_g3to6_L1_percent, self.math_g3to6_L1_percent,
                                        self.g1to6_class_size,
                                        self.per_free_lunch, self.per_reduced_lunch)
