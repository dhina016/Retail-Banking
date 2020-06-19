import os, time
from datetime import datetime
from flask import Flask, request, render_template, flash, redirect, url_for, session, logging, jsonify
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from forms import LoginForm, CreateCustomer, UpdateCustomer, DepositAmount, CashTransfer, CreateAccount, UpdateAccount, WithdrawAmount, CreateExecutive, CustomerAccount

app = Flask(__name__)

app.secret_key = 'retailBanking'

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_DB'] = 'retailbank'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        username = request.form['username']
        user_pass = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM userstore WHERE username = %s AND isActive = 'active' AND isDel = 0",[username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            userlevel = data['userlevel']
            if userlevel == 0:
                permission = 'Admin'
            elif userlevel == 1:
                permission = 'Excecutive'
            elif userlevel == 2:
                permission = 'Cashier'
            else:
                permission = 'User'
            if sha256_crypt.verify(user_pass, password):
                session['logged_in']    = True
                session['userlevel']    = userlevel
                session['username']     = username
                session['permission']   = permission
                flash('Logged In Successfully!!!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid Login', 'danger')
                return redirect(url_for('login'))
        else:
            flash('User Not Found', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html',form=form)

@app.route('/logout')
def logout():
    session.pop('logged_in',False)
    session.pop('permission',False)
    session.pop('username',False)
    session.pop('userlevel',False)
    return redirect(url_for('login'))

@app.route('/custlogin',methods=["POST"])
def custlogin():
    if request.method == 'POST':
        username = request.form['username']
        user_pass = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM customer WHERE customerID = %s AND isActive = 0 AND isDel = 0",[username])
        if result > 0:
            data = cur.fetchone()
            name = data['name']
            result = cur.execute("SELECT * FROM customerlogin WHERE customerID = %s",[username])
            if result > 0:
                data = cur.fetchone()
                password = data['password']
                if sha256_crypt.verify(user_pass, password):
                    session['check_in']    = True
                    session['name']     = username
                    session['user']     = name
                    return redirect(url_for('custdashboard'))
                else:
                    flash('Invalid Login', 'danger')
                    return redirect(url_for('home'))
            else:
                flash('Invalid Login', 'danger')
                return redirect(url_for('home'))
        else:
            flash('User Not Found', 'danger')
            return redirect(url_for('home'))

@app.route('/custlogout')
def custlogout():
    session.pop('check_in',False)
    session.pop('name',False)
    flash('Logged Out Successfully!!!', 'success')
    return redirect(url_for('home'))

#dashboard
@app.route('/dashboard')
def dashboard():
    if session.get('logged_in') and (session.get('userlevel') == 0 or session.get('userlevel') == 1 or session.get('userlevel') == 2):
        title = ['Dashboard','All Details Available','']
        cur = mysql.connection.cursor()
        cur.execute("SELECT count(*) as total, 'Transaction' as t from transaction")
        a = cur.fetchone()
        cur.execute("SELECT count(*) as total, 'Deposit' as t from deposit")
        b = cur.fetchone()
        cur.execute("SELECT count(*) as total, 'Withdraw' as t from withdraw")
        c = cur.fetchone()
        cur.execute("SELECT count(*) as total from account where isDel = 0 AND status = 'active'")
        d = cur.fetchone()
        cur.execute("SELECT count(*) as total from account where isDel <> 0 or status <> 'active'")
        e = cur.fetchone()
        cur.execute("SELECT count(*) as total from customer where isDel = 0 AND isActive = 0")
        f = cur.fetchone()
        cur.execute("SELECT count(*) as total from customer where isDel <> 0 or isActive <> 0")
        g = cur.fetchone()
        l = [a,b,c,d,e,f,g]
        return render_template('dashboard.html',title=title, detail=l)
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))


@app.route('/custdashboard')
def custdashboard():
    if session.get('check_in'):
        cur = mysql.connection.cursor()
        cur.execute('''SELECT  accountID  as accid ,if( accountType = 'S','Savings','Current') as type,  amount ,  depositDate  as date, 'deposit' as description FROM  deposit where customerID = %s
            UNION ALL
            SELECT  accountID  as accid ,if( accountType = 'S','Savings','Current') as type,  amount ,  withdrawDate  as date, 'withdraw' as description FROM  withdraw where customerID = %s
            UNION ALL
            SELECT  sourceaccountid  as accid ,if( sourceAccType = 'S','Savings','Current') as type,  amount ,  transactionDate  as date, 'transaction' as description FROM  transaction where customerID = %s''',[session.get('name'), session.get('name'), session.get('name')])
        detail = cur.fetchall()
        cur.execute(''' select AccountBalance from account where customerID = %s and accountType =%s ''',[session.get('name'), 'S'])
        saving = cur.fetchone()
        cur.execute(''' select AccountBalance from account where customerID = %s and accountType =%s ''',[session.get('name'), 'C'])
        current = cur.fetchone()
        return render_template('custdashboard.html',detail=detail, c=current, s=saving)
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

#Customer section
@app.route('/createCustomer',methods=["GET","POST"])
def createcustomer():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):    
            form = CreateCustomer()
            title = ['Create Customer','Fill all the fields to create customer','']
            if request.method == 'POST' and form.validate():
                ssnid = form.ssnid.data
                name = form.name.data
                age = form.age.data
                address = form.address.data
                state = form.state.data
                city = form.city.data
                generate = str(int(time.time()))
                id = int(generate[0:1]+generate[2:])
                state = form.state.data
                city = form.city.data

                cur = mysql.connection.cursor()
                checkcustomer= cur.execute("select SSNID from customer where SSNID = %s ",[ssnid])
                if checkcustomer == False:
                    if(cur.execute('''Insert into customer (customerID, SSNID, name, address, age, state, city) VALUES (%s, %s, %s, %s, %s, %s, %s)''', ( id, ssnid, name, address, age, state, city))):
                        mysql.connection.commit()
                        cur.close()
                        flash('Created Successfully!!', 'success')
                        return redirect('createCustomer')
                    else:
                        flash('Something went wrong', 'danger')
                        return redirect('createCustomer')
                else:
                    flash(f"Customer account with SSN ID - {ssnid} already exists !", "danger")
                    return redirect(url_for('createcustomer'))

            return render_template('create_customer.html',title=title,form=form)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/updatecustomerdetails')
def updatecustomerdetails():
    if session.get('logged_in'):
        if (session.get('userlevel') == 0 or session.get('userlevel') == 1):    
            title = ['Manage Customer','List of all Customer','']
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from customer where isDel = 0")
            detail = cur.fetchall()
            return render_template('manage_customer.html',title=title, detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/getcustomerdetail',methods=["GET"])
def getcustomerdetail():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from customer where customerID = %s", [ request.args.get('cid') ])
            detail = cur.fetchone()
            return jsonify(detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/editcustomerdetail/<id>',methods=["GET","POST"])
def editcustomerdetail(id):
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            detail = None
            title = ['Update Customer','Edit Customer Details','']
            cur = mysql.connection.cursor()
            form = UpdateCustomer()
            if(request.method == "GET"):
                cur.execute("SELECT * from customer where customerID = %s", [ id ])
                detail = cur.fetchone()
            if(request.method == 'POST') and form.validate():
                name = request.form['name']
                age = request.form['age']
                address = request.form['address']
                active = request.form['active']
                id = request.form['id']
                message = request.form['message']
                check = cur.execute("UPDATE customer SET name = %s, address = %s, age = %s, isActive = %s, message= %s where customerID = %s", ( name, address, age, active, message, id ))
                if(check):
                    mysql.connection.commit()
                    flash('Updated Successfully!!', 'success')
                    return redirect(url_for("updatecustomerdetails"))
                else:
                    flash('No row Affected or Something Went Wrong', 'danger')
                    return redirect(url_for("updatecustomerdetails"))
                    
            return render_template('edit_customer.html',form=form,title=title,detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/deletecustomerdetail/<id>',methods=["PUT"])
def deletecustomerdetail(id):
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            cur = mysql.connection.cursor()
            check = cur.execute("UPDATE customer SET isDel = %s where customerID = %s",( 1, id ))
            mysql.connection.commit()
            if(check):
                return jsonify('true')
            else:
                return False
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/customerstatus')
def customerstatus():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            title = ['Customer Status','Status of all Customer Here','']
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from customer where isDel = 0")
            detail = cur.fetchall()
            return render_template('status_customer.html',title=title, detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

#Accounts section
@app.route('/getaccountdetail',methods=["GET"])
def getaccountdetail():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            cur = mysql.connection.cursor()
            cur.execute("SELECT count(customerID) as total from account where customerID = %s AND status = %s AND isDel = %s", [ request.args.get('cid'),'active', 0])
            detail = cur.fetchone()
            return jsonify(detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/selectaccountdetail',methods=["GET"])
def selectaccountdetail():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            cur = mysql.connection.cursor()
            cur.execute("SELECT accountType,accountID,AccountBalance from account where customerID = %s AND accountType = %s AND status = %s AND isDel = %s", [ request.args.get('cid'), request.args.get('type'),'active', 0 ])
            detail = cur.fetchone()
            return jsonify(detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/getaccount',methods=["GET"])
def getaccount():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from account where accountId = %s", [ request.args.get('cid')])
            detail = cur.fetchone()
            return jsonify(detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/deleteaccount/<id>',methods=["PUT"])
def deleteaccount(id):
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            cur = mysql.connection.cursor()
            check = cur.execute("UPDATE account SET isDel = %s where accountID = %s",( 1, id ))
            mysql.connection.commit() 
            if(check):
                return jsonify('true')
            else:
                return False
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/updateaccountdetails')
def updateaccountdetails():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            title = ['Manage Account','List of all Account','']
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from account where isDel = 0")
            detail = cur.fetchall()
            return render_template('manage_account.html',title=title, detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/editaccount/<id>',methods=["GET","POST"])
def editaccount(id):
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            detail = None
            title = ['Update Account','Edit Account details','']
            cur = mysql.connection.cursor()
            form = UpdateAccount()
            if(request.method == "GET"):
                cur.execute("SELECT * from account where accountID = %s", [ id ])
                detail = cur.fetchone()
            if(request.method == 'POST') and form.validate():
                active = request.form['active']
                id = request.form['id']
                message = request.form['message']
                check = cur.execute("UPDATE account SET status = %s, message= %s where accountID = %s", ( active, message, id ))
                mysql.connection.commit()
                if(check):
                    flash('Updated Successfully!!', 'success')
                    return redirect(url_for("updateaccountdetails"))
                else:
                    flash('Something Went Wrong', 'danger')
                    return redirect(url_for("updateaccountdetails"))
            else:     
                return render_template('edit_account.html',form=form,title=title,detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/accountstatus')
def accountstatus():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            title = ['Account Status','Status of Accounts Here','']
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from account where isDel = 0")
            detail = cur.fetchall()
            return render_template('status_account.html',title=title, detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/createaccount',methods=["GET","POST"])
def createaccount():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 1):
            form = CreateAccount()
            if request.method == 'POST':
                customerID = form.customerID.data
                generate = str(int(time.time()))
                accountID = int(generate[1:])+100000000
                accounttype     =   form.AccountType.data
                DepositAmount   =   form.DepositAmount.data
                cur = mysql.connection.cursor()
                #check if customer account exists in customer table
                checkaccount    = cur.execute("select customerID from customer where customerID = %s ",[customerID])
                if checkaccount == True:
                    #check if  account exists in accounts table
                    checkaccounttype=cur.execute("select accountType,customerID from account where customerID = %s and accountType=%s",[customerID,accounttype])
                    if checkaccounttype==False:
                        if cur.execute('''Insert into account (customerID, accountID, accountType,AccountBalance) VALUES (%s, %s, %s,%s)''', (customerID, accountID, accounttype,DepositAmount)):
                            mysql.connection.commit()
                            cur.close()
                            flash(f"Customer account with  {customerID} and account type {accounttype}created successfully!", "success")
                            return redirect(url_for('createaccount'))
                        else:
                            flash(f"Their was error in Customer account creation with ssnid {customerID} !", "danger")
                            return redirect(url_for('createaccount'))
                    else:
                        flash(f"Customer account with {customerID}   and account type {accounttype} already exists !", "danger")
                        return redirect(url_for('createaccount'))        

                else:
                    flash(f"Customer account with {customerID} does not exists !", "danger")
                    return redirect(url_for('createaccount'))    

            cur = mysql.connection.cursor()
            cur.execute("select customerID,name from customer where isDel = 0 AND isActive = 0")
            customerIDList = cur.fetchall() 
            title = ['Create Account','Fill All fields to Create Account']
            return render_template('createaccount.html',form=form, title=title, customerIDList=customerIDList)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

#Transaction section
@app.route('/cashtransfer',methods=["GET","POST"])
def cashtransfer():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            SourceAccountIDBalList=[]
            form = CashTransfer()
            if request.method == 'POST':
                customerID          =   form.CustomerID.data
                SourceAccountType   =   form.SourceAccountType.data
                TargetAccountType   =   form.TargetAccountType.data
                TransferAmount      =   form.TransferAmount.data
                cur = mysql.connection.cursor()
                cur.execute("select accountID,AccountBalance from account where accountType = %s and customerID = %s ",[SourceAccountType,customerID])
                SourceAccountIDBalList = cur.fetchone() 
                SourceAccountBalance     =   SourceAccountIDBalList['AccountBalance']
                SourceAccountID          =   SourceAccountIDBalList['accountID']

                # check if sufficient account Balance in source account
                if TransferAmount <= SourceAccountBalance:
                    #update target account Balance
                    cur.execute("select accountID,AccountBalance from account where accountType = %s and customerID = %s",[TargetAccountType,customerID])
                    TargetAccountIDBalList = cur.fetchone() 
                    targetAccountBalance  =   TargetAccountIDBalList['AccountBalance']
                    targetAccountID       =   TargetAccountIDBalList['accountID']
                    targetAccountBalance += TransferAmount
                    cur.execute('''Update account SET AccountBalance = %s, message = %s  where accountID = %s''', (targetAccountBalance, 'Amount Recieved', targetAccountID))
                    SourceAccountBalance -= TransferAmount
                    cur.execute('''Update account SET AccountBalance = %s, message = %s  where accountID = %s''', (SourceAccountBalance, 'Amount Transfered', SourceAccountID))
                    
                    #update transaction in deposit table
                    if cur.execute('''Insert into transaction (customerID,sourceaccountid,targetaccountid,amount,sourceAccType,targetAccType) VALUES (%s, %s, %s, %s, %s, %s)''', (customerID, SourceAccountID,targetAccountID,TransferAmount,SourceAccountType,TargetAccountType)):
                        mysql.connection.commit()
                        cur.close()
                        flash(f"Amount of {TransferAmount} of account id {SourceAccountID} transfered to account  {targetAccountID}  ", "success")
                        return redirect(url_for('cashtransfer'))    
                    else:
                        flash(f"Transfer Declined", "danger")    
                else:
                    flash(f"Insufficient Balance Encountered!", "danger")
            cur = mysql.connection.cursor()
            cur.execute("select customerID,name from customer where isActive = 0 AND isDel = 0")
            customerIDList = cur.fetchall() 
            title = ['Transfer','Transfer Your cash Here']
            return render_template('cashtransfer.html',title=title,form=form,customerIDList=customerIDList)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/deposit/<id>',methods=['GET','POST'])
def deposit(id):
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            form = DepositAmount()
            title = ['Deposit','Deposit Amount Here']
            cur = mysql.connection.cursor()
            if(request.method == "GET"):
                cur.execute("SELECT * from account where accountID = %s", [ id ])
                detail = cur.fetchone()
            if(request.method == 'POST') and form.validate():
                id = request.form['id']
                cur.execute("select * from account where accountID = %s ",[ id ])
                accdetail = cur.fetchone()
                acctype=accdetail['accountType']
                cusid=accdetail['customerID']
                amount = request.form['DepositAmount']
                balance = float(amount) + float(accdetail['AccountBalance'])
                if(cur.execute('''Update account SET AccountBalance = %s, message = %s  where accountID = %s''', (balance, 'Amount Deposited', id))):       
                    cur.execute('''Insert into deposit (customerID, accountID, accountType, amount) VALUES (%s, %s, %s, %s)''', (cusid,id,acctype,amount))
                    mysql.connection.commit()
                    flash('Deposited Successfully', 'success')
                    return redirect(url_for("withdrawmoney"))
                else:
                    flash('Something Went Wrong', 'danger')
                    return redirect(url_for("withdrawmoney"))

            return render_template('deposit.html',title=title,form=form,detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/withdraw/<id>',methods=['GET','POST'])
def withdraw(id):
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            form = WithdrawAmount()
            title = ['Withdraw','Withdraw Amount Here']
            cur = mysql.connection.cursor()
            if(request.method == "GET"):
                cur.execute("SELECT * from account where accountID = %s", [ id ])
                detail = cur.fetchone()
            if(request.method == 'POST') and form.validate():
                id = request.form['id']
                cur.execute("select * from account where accountID = %s ",[ id ])
                accdetail = cur.fetchone()
                amount = request.form['WithdrawAmount']
                acctype=accdetail['accountType']
                cusid=accdetail['customerID']
                amount = request.form['WithdrawAmount']
                if(float(amount) <= float(accdetail['AccountBalance'])):
                    balance = float(accdetail['AccountBalance']) - float(amount)
                    if(cur.execute('''Update account SET AccountBalance = %s, message = %s  where accountID = %s''', (balance, 'Amount Withdrawn', id))):       
                        cur.execute('''Insert into withdraw (customerID, accountID, accountType, amount) VALUES (%s, %s, %s, %s)''', (cusid,id,acctype,amount))
                        mysql.connection.commit()
                        flash('Withdraw Successfully', 'success')
                        return redirect(url_for("withdrawmoney"))
                    else:
                        flash('Something Went Wrong', 'danger')
                        return redirect(url_for("withdrawmoney"))
                else:
                    flash('Insufficient Balance', 'danger')
                    return redirect(url_for("withdrawmoney"))

            return render_template('withdraw.html',title=title,form=form,detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/withdrawmoney')
def withdrawmoney():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            title = ['Manage Transaction','Select Deposit or Withdraw']
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from account where status='active' AND isDel = 0")
            detail = cur.fetchall()
            return render_template('withdrawmoney.html',title=title, detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

#Report Section
@app.route('/singlereport')
def singlereport():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):    
            title = ['Specific Report','Generate Repote Here','datatable']
            cur = mysql.connection.cursor()
            cur.execute("select account.accountID, customer.name from account inner join customer on customer.customerID = account.customerID ")
            #cur.execute("select account.accountID, customer.name from account inner join customer on customer.customerID = account.customerID where account.isDel = 0 AND account.status = 'active' AND customer.isActive = 0 AND customer.isDel = 0")
            detail = cur.fetchall()
            return render_template('specific.html',title=title,detail=detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/singlereportdate')
def singlereportdate():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):    
            cur = mysql.connection.cursor()
            fromDate = datetime.strptime(request.args.get("from"), '%m/%d/%Y').strftime('%Y-%m-%d')
            toDate = datetime.strptime(request.args.get("to"), '%m/%d/%Y').strftime('%Y-%m-%d')
            aid = request.args.get("id")
            cur.execute('''SELECT  accountID  as accid ,if( accountType = 'S','Savings','Current') as type,  amount ,  depositDate  as date, 'deposit' as description FROM  deposit where accountID = %s AND depositDate between %s and %s
            UNION ALL
            SELECT  accountID  as accid ,if( accountType = 'S','Savings','Current') as type,  amount ,  withdrawDate  as date, 'withdraw' as description FROM  withdraw where accountID = %s AND withdrawDate between %s and %s
            UNION ALL
            SELECT  sourceaccountid  as accid ,if( sourceAccType = 'S','Savings','Current') as type,  amount ,  transactionDate  as date, 'transaction' as description FROM  transaction where sourceaccountid = %s AND transactionDate between %s and %s''',[aid, fromDate, toDate,aid, fromDate, toDate,aid, fromDate, toDate])
            detail = cur.fetchall()
            return jsonify(detail)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/singlereportlast')
def singlereportlast():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            cur = mysql.connection.cursor()
            aid = request.args.get("id")
            cur.execute('''SELECT  accountID  as accid ,if( accountType = 'S','Savings','Current') as type,  amount ,  depositDate  as date, 'deposit' as description FROM  deposit  where accountID = %s order by atTime,date DESC''',[aid])
            deposit = cur.fetchone()
            cur.execute('''SELECT  accountID  as accid ,if( accountType = 'S','Savings','Current') as type,  amount ,  withdrawDate  as date, 'withdraw' as description FROM  withdraw where accountID = %s order by atTime,date DESC''',[aid])
            withdraw = cur.fetchone()
            cur.execute('''SELECT  sourceaccountid  as accid ,if( sourceAccType = 'S','Savings','Current') as type,  amount ,  transactionDate  as date, 'transaction' as description FROM  transaction where sourceaccountid = %s order by atTime,date DESC''',[aid])
            transfer = cur.fetchone()
            return jsonify(deposit,withdraw,transfer)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/report')
def report():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            title = ['General Report','Generate Repote Here','datatable']
            return render_template('report.html',title=title)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/reportdate',methods=['GET'])
def reportdate():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            fromDate = datetime.strptime(request.args.get("from"), '%m/%d/%Y').strftime('%Y-%m-%d')
            toDate = datetime.strptime(request.args.get("to"), '%m/%d/%Y').strftime('%Y-%m-%d')
            field = request.args.get("field")
            cur = mysql.connection.cursor()
            if(field == 'customer'):
                cur.execute("SELECT * from customer where createAt BETWEEN %s AND %s", [ fromDate, toDate ])
            elif(field == 'account'):
                cur.execute("SELECT * from account where createAt BETWEEN %s AND %s", [ fromDate, toDate ])
            elif(field == 'deposit'):
                cur.execute("SELECT id,customerID,accountID,accountType,amount,depositDate from deposit where depositDate BETWEEN %s AND %s", [ fromDate, toDate ])
            elif(field == 'withdraw'):
                cur.execute("SELECT id,customerID,accountID,accountType,amount,withdrawDate from withdraw where withdrawDate BETWEEN %s AND %s", [ fromDate, toDate ])
            elif(field == 'transfer'):
                cur.execute("SELECT id,customerID,amount,sourceaccountid,targetaccountid,transactionDate from transaction where transactionDate BETWEEN %s AND %s", [ fromDate, toDate ])
            check = cur.fetchall()
            if(check):
                return jsonify(check)
            else:
                return jsonify(None)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/reportaccount')
def reportaccount():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            title = ['Manage Customer','This is Create Customer','datatable']
            return render_template('reportaccount.html',title=title)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

@app.route('/reportaccountdate',methods=['GET'])
def reportaccountdate():
    if session.get('logged_in'):
        if  (session.get('userlevel') == 0 or session.get('userlevel') == 2):
            fromDate = datetime.strptime(request.args.get("from"), '%m/%d/%Y').strftime('%Y-%m-%d')
            toDate = datetime.strptime(request.args.get("to"), '%m/%d/%Y').strftime('%Y-%m-%d')
            cur = mysql.connection.cursor()
            cur.execute("SELECT * from account where createAt BETWEEN %s AND %s", [ fromDate, toDate ])
            check = cur.fetchall()
            if(check):
                return jsonify(check)
            else:
                return jsonify(None)
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

#Create executive
@app.route('/CreateExecutive',methods=["GET","POST"])
def createexecutive():
    if session.get('logged_in'):
        if (session.get('userlevel') == 0):
            form = CreateExecutive()
            title = ['Create Executive','Create Executive or Cashier account','']
            if request.method == 'POST' and form.validate():
                username    =   form.username.data
                name        =   form.name.data
                address     =   form.address.data
                phone       =   form.phone.data
                password = sha256_crypt.encrypt(str(form.password.data))
                userlevel   =   form.userlevel.data

                cur = mysql.connection.cursor()
                checkexecutive= cur.execute("select username from userdetail where username = %s ",[username])
                if checkexecutive == False:
                        if(cur.execute('''Insert into userdetail (username, name, address,phone) VALUES (%s, %s, %s, %s)''', (username, name, address,phone)) and cur.execute('''Insert into userstore  (username,password,userlevel,isActive) VALUES (%s, %s, %s,%s)''', (username,password,userlevel,"active"))):
                            mysql.connection.commit()
                            cur.close()
                            flash('Created Successfully!!', 'success')
                            return redirect('CreateExecutive')
                        else:
                            flash('Something went wrong', 'danger')
                            return redirect('CreateExecutive')
                else:
                    flash(f"CreateExecutive account with username - {username} already exists !", "danger")
                    return redirect(url_for('createexecutive'))

            return render_template('createexecutive.html',title=title,form=form)  
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

#Create user
@app.route('/usercreate',methods=["GET","POST"])
def usercreate():
    if session.get('logged_in'):
        if (session.get('userlevel') == 0):
            form = CustomerAccount()
            if request.method == 'POST' :
                customerID   =   form.customerID.data
                password     =   sha256_crypt.encrypt(str(form.password.data))
                cur = mysql.connection.cursor()
                checkaccount= cur.execute("select customerID from customerlogin where customerID = %s ",[customerID])
                if checkaccount == False:
                        if(cur.execute('''Insert into customerlogin (customerID,password) VALUES (%s, %s)''', (customerID,password))):
                            mysql.connection.commit()
                            cur.close()
                            flash('Created Successfully!!', 'success')
                            return redirect('usercreate')
                        else:
                            flash('Something went wrong', 'danger')
                            return redirect('usercreate')
                else:
                    flash(f"Account with customerID - {customerID} already exists !", "danger")
                    return redirect(url_for('usercreate'))  
            cur = mysql.connection.cursor()
            cur.execute("select customerID,name from customer where isDel = 0 AND isActive = 0 AND customerID NOT IN (select customerID from customerlogin ) ")
            customerIDList = cur.fetchall() 
            title = ['Create Customer Account','Create Customer Account Here']
            return render_template('customeraccount.html',form=form, title=title, customerIDList=customerIDList)    
        else:
            flash('Session Timeout', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('logout'))

#Custom Error
@app.errorhandler(404)
def page_not_found(e):
    return render_template('pages-404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('pages-500.html'), 500

@app.errorhandler(403)
def page_forbidden(e):
    return render_template('pages-403.html'), 403

if __name__ == "__main__":
    app.secret_key = 'retailBanking'
    app.run(debug = True)