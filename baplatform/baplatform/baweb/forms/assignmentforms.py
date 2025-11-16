from baweb import models
from ..utils.bootstrap import BootStrapModelForm

class AssignmentFileForm(BootStrapModelForm):
    class Meta:
        model = models.AssignmentFile
        fields = ['file', 'file_name']


class AssignmentCommentForm(BootStrapModelForm):
    class Meta:
        model = models.AssignmentComment
        fields = ['comment']


class AssignmentSubmitForm(BootStrapModelForm):
    class Meta:
        model = models.AssignmentSubmit
        fields = ['file', 'file_name']

class AssignmentMarkForm(BootStrapModelForm):
    class Meta:
        model = models.AssignmentSubmit
        fields = ['marks', 'max_marks']