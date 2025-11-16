from django import forms
from django.core.exceptions import ValidationError

from baweb import models
from baweb.utils.bootstrap import BootStrapForm, BootStrapModelForm
from ..utils.encrypt import md5

class UserModelForm(BootStrapModelForm):
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(render_value=True)
    )
    class Meta:
        model = models.User
        fields = ['username', 'password', 'confirm_password', 'type']
        widgets = {
            'password': forms.PasswordInput(render_value=True)
        }

    def clean_password(self):
        pwd = self.cleaned_data.get('password')
        return md5(pwd)

    def clean_confirm_password(self):
        pwd = self.cleaned_data.get('password')
        confirm = md5(self.cleaned_data.get('confirm_password'))
        if confirm != pwd:
            raise ValidationError("密码不一致")
        return confirm

class UserLoginForm(BootStrapForm):
    username = forms.CharField(
        label="用户名",
        widget = forms.TextInput,
        required=True
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(render_value=True),
        required=True
    )
    code = forms.CharField(
        label="验证码",
        widget = forms.TextInput,
        required=True
    )
    fields =  ['username', 'password', 'code']
    def clean_password(self):
        pwd = self.cleaned_data.get('password')
        return md5(pwd)

class UserChangePasswordForm(BootStrapForm):
    password = forms.CharField(
        label="新密码",
        widget=forms.PasswordInput(render_value=True),
        required=True
    )
    confirm_password = forms.CharField(
        label="确认新密码",
        widget=forms.PasswordInput(render_value=True), 
        required=True
    )
    fields =  ['password', 'confirm_password']
    def clean_password(self):
        pwd = self.cleaned_data.get('password')
        return md5(pwd)

    def clean_confirm_password(self):
        pwd = self.cleaned_data.get('password')
        confirm = md5(self.cleaned_data.get('confirm_password'))
        if confirm != pwd:
            raise ValidationError("密码不一致")
        return confirm
