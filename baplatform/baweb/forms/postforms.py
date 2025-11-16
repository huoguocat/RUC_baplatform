from django import forms
from baweb import models
from ..utils.bootstrap import BootStrapModelForm


class PostCreateForm(BootStrapModelForm):
    '''创建帖子表单'''
    tags = forms.CharField(
        label='标签',
        max_length=512,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '多个标签用逗号分隔，如: Python,Django,Web开发'})
    )
    
    class Meta:
        model = models.Post
        fields = ['title', 'content', 'category', 'tags', 'isAnonymous']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '请输入帖子标题...', 'maxlength': 256}),
            'content': forms.Textarea(attrs={'placeholder': '请输入帖子内容...', 'rows': 8}),
            'isAnonymous': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # category 字段处理
        self.fields['category'].queryset = models.ContentCategory.objects.all()
        self.fields['category'].label = '内容分类'


class PostUpdateForm(BootStrapModelForm):
    '''更新帖子表单'''
    tags = forms.CharField(
        label='标签',
        max_length=512,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '多个标签用逗号分隔'})
    )
    
    class Meta:
        model = models.Post
        fields = ['title', 'content', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': 256}),
            'content': forms.Textarea(attrs={'rows': 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = models.ContentCategory.objects.all()


class PostCommentForm(BootStrapModelForm):
    '''创建评论表单'''
    
    class Meta:
        model = models.PostComment
        fields = ['content', 'isAnonymous']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': '请输入你的评论...',
                'rows': 4,
                'style': 'resize: vertical;'
            }),
            'isAnonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = '评论内容'
        self.fields['isAnonymous'].label = '是否匿名评论'


class PostSearchForm(forms.Form):
    '''帖子搜索表单'''
    SORT_CHOICES = (
        ('heat', '按热度排序'),
        ('newest', '按最新排序'),
        ('popular', '按热门排序'),
    )
    
    keyword = forms.CharField(
        label='搜索关键词',
        max_length=256,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '输入搜索关键词...'})
    )
    
    category = forms.ModelChoiceField(
        label='内容分类',
        queryset=models.ContentCategory.objects.all(),
        required=False,
        empty_label='所有分类'
    )
    
    sort_by = forms.ChoiceField(
        label='排序方式',
        choices=SORT_CHOICES,
        required=False,
        initial='heat'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap样式
        for field in self.fields.values():
            if field.widget.attrs:
                field.widget.attrs["class"] = "form-control"
            else:
                field.widget.attrs = {"class": "form-control"}
