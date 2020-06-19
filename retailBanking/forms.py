from flask_wtf import FlaskForm
from wtforms import Form, validators
from wtformsparsleyjs import IntegerField,FloatField, BooleanField, SelectField, StringField, PasswordField, TextAreaField, RadioField
 


class LoginForm(FlaskForm):
    username   = StringField("username", [ validators.DataRequired(message="Username is Required"), validators.Length(message='UserName should be Minimun 4 characters.',
                          min=4) ] )
    password = PasswordField("Password", [ validators.DataRequired(message="Password is Required"), validators.Length(message='Password should be and 5 characters.',
                          min=5),validators.Regexp(message=' Password should contain 5 characters including one special character, one upper case, one numeric.',
                          regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[\W\_])[A-Za-z\d\W\_]*$'), ] )


class CreateCustomer(FlaskForm):
    ssnid = IntegerField("SSN ID", [validators.DataRequired(message="SSN ID is Required"), validators.NumberRange(message='SSN should be exactly 9', min=100000000, max=999999999) ])
    name = StringField("Name", [validators.DataRequired(message="Name is Required"), validators.Regexp(message='Name should only alphabet', regex=r'^[a-zA-Z ]*$') , validators.Length(message='Name should only alphabet and minimum 3 character', min=3, max=25) ] )
    age = IntegerField("Age", [validators.DataRequired(message="Age is Required"), validators.NumberRange(message='Minimum age is 10', min=10, max=120) ])
    address = StringField("Address", [ validators.DataRequired(message="Address is Required") ])
    state = StringField()
    city = StringField()

class UpdateCustomer(FlaskForm):
    name = StringField("Name", [validators.DataRequired(message="Name is Required"), validators.Regexp(message='Name should only alphabet', regex=r'^[a-zA-Z ]*$') , validators.Length(message='Name should only alphabet and minimum 3 character', min=3, max=25) ] )
    age = IntegerField("Age", [validators.DataRequired(message="Age is Required"), validators.NumberRange(message='Minimum age is 10', min=10, max=120) ])
    address = StringField("Address", [ validators.DataRequired(message="Address is Required") ] )
    message = StringField("Message", [ validators.DataRequired(message="Message is Required") ] )


class CreateAccount(FlaskForm):
    customerID      = IntegerField("CustomerID",   [validators.DataRequired(message="CustomerID  is Required")] )
    AccountType     = StringField("AccountType",   [validators.DataRequired(message="AccountType is Required")])
    DepositAmount   = FloatField("DepositAmount", [validators.DataRequired(message="DepositAmount is Required")])

class CashTransfer(FlaskForm):
    CustomerID            = IntegerField("CustomerID",   [validators.DataRequired(message="CustomerID  is Required")])
    SourceAccountType     = StringField("SourceAccountType",   [validators.DataRequired(message="SourceAccountType is Required")])
    TargetAccountType     = StringField("TargetAccountType",   [validators.DataRequired(message="TargetAccountType is Required")])
    TransferAmount        = FloatField("TransferAmount",       [validators.DataRequired(message="TransferAmount is Required")])     

class UpdateAccount(FlaskForm):
    message = StringField("Message", [ validators.DataRequired(message="Message is Required") ] )

class DepositAmount(FlaskForm):
    DepositAmount = FloatField("TransferAmount", [validators.DataRequired(message="DepositAmount is Required"), validators.NumberRange(message='Minimum Rs.1', min=1) ])     
 
class WithdrawAmount(FlaskForm):
    WithdrawAmount = FloatField("TransferAmount", [validators.DataRequired(message="WithdrawAmount is Required"), validators.NumberRange(message='Minimum Rs.1', min=1) ])     
 
class CreateExecutive(FlaskForm):
    username      = StringField("username",   [ validators.DataRequired(message="Username is Required"), validators.Length(message='UserName should be Minimun 4 characters.',min=4) ] )
    name          = StringField("name",       [validators.DataRequired(message="name  is Required")] )
    address       = StringField("address",    [validators.DataRequired(message="address  is Required")] )
    phone         = StringField("phone",      [validators.DataRequired(message="Mobile Number  is Required")] )
    password      = PasswordField("password",   [ validators.DataRequired(message="Password is Required"), validators.Length(message='Password should be and 5 characters.',
                          min=5),validators.Regexp(message=' Password should contain 5 characters including one special character, one upper case, one numeric.',
                          regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[\W\_])[A-Za-z\d\W\_]{5,}$') ] )
    userlevel     = IntegerField("userlevel",  [validators.DataRequired(message="Userlevel is Required")])  

class CustomerAccount(FlaskForm):
    customerID   = IntegerField("CustomerID",   [validators.DataRequired(message="CustomerID  is Required")])     
    password     = PasswordField("Password", [ validators.DataRequired(message="Password is Required"), validators.Length(message='Password should be and 5 characters.',
                          min=5),validators.Regexp(message=' Password should contain 5 characters including one special character, one upper case, one numeric.',
                          regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[\W\_])[A-Za-z\d\W\_]{5,}$') ] )