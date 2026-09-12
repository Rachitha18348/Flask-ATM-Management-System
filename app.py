
from flask import Flask, render_template, redirect, request, url_for, session
import json
from mail import send_email
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'atm@26'


def generate_otp():
    return str(random.randint(100000, 999999))


def get_data():
    with open('data.json', 'r') as file:
        data = json.load(file)
        return data


def update_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)


@app.route('/')
def base():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():

    info = request.args.get('info')

    if request.method == 'POST':

        email = request.form.get('email')
        pin = request.form.get('pin')

        data = get_data()
        users = data["users"]

        for i in users:

            if email == i["email"] and pin == i["pin"]:

                session['name'] = i["name"]
                session['id'] = i["id"]

                return redirect('/dashboard')

        return redirect(
            url_for('login', info='Invalid Login')
        )

    return render_template('login.html', info=info)


@app.route('/register', methods=['GET', 'POST'])
def register():

    info = request.args.get('info')

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        pin = request.form.get('pin')
        cpin = request.form.get('cpin')

        data = get_data()
        users = data["users"]

        for i in users:

            if i["email"] == email:
                return redirect(
                    url_for(
                        'register',
                        info="Email is already registered"
                    )
                )

        if pin != cpin:
            return redirect(
                url_for(
                    'register',
                    info="Enter the pin properly"
                )
            )

        userinfo = {
            "id": len(users) + 1,
            "name": name,
            "email": email,
            "pin": pin,
            "balance": 0,
            "history": []
        }

        users.append(userinfo)
        update_data(data)

        return redirect(
            url_for(
                'login',
                info="Successfully Registered"
            )
        )

    return render_template('register.html', info=info)


@app.route('/forgotpin', methods=['GET', 'POST'])
def forgotpin():

    info = request.args.get('info')

    if request.method == 'POST':

        email = request.form.get('email')

        data = get_data()
        users = data["users"]

        for i in users:

            if i["email"] == email:

                username = i["name"]

                session["email"] = i["email"]

                otp = generate_otp()
                session['otp'] = otp

                send_email(email, username, otp)

                return redirect('/verify')

        return redirect(
            url_for(
                'forgotpin',
                info="Email is not registered"
            )
        )

    return render_template('forgotpin.html', info=info)


@app.route('/resetpin', methods=['GET', 'POST'])
def resetpin():

    info = request.args.get('info')

    if request.method == 'POST':

        npin = request.form.get('npin')
        cpin = request.form.get('cpin')

        if npin == cpin:

            data = get_data()
            users = data["users"]

            for i in users:

                if i["email"] == session["email"]:

                    i["pin"] = npin

                    update_data(data)

                    session.pop('email', None)

                    return redirect(
                        url_for(
                            'login',
                            info='Reset pin is successful, now you can login'
                        )
                    )

        return redirect(
            url_for(
                'resetpin',
                info='Incorrect Pin'
            )
        )

    return render_template('resetpin.html', info=info)


@app.route('/verify', methods=['GET', 'POST'])
def verify():

    info = request.args.get('info')

    if request.method == 'POST':

        otp = request.form.get('otp')

        if otp == session.get('otp'):

            session.pop('otp', None)

            return redirect(
                url_for(
                    'resetpin',
                    info='OTP verification done'
                )
            )

        return redirect(
            url_for(
                'verify',
                info="Invalid OTP"
            )
        )

    return render_template('verify.html', info=info)


@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


@app.route('/dashboard')
def dashboard():

    if 'id' not in session:
        return redirect('/login')

    return render_template('dashboard.html')


@app.route('/checkbalance')
def checkbalance():

    if 'id' not in session:
        return redirect('/login')

    data = get_data()
    users = data["users"]

    for i in users:

        if i["id"] == session["id"]:

            balance = i["balance"]

            return render_template(
                'checkbalance.html',
                balance=balance
            )

    return redirect('/login')


@app.route('/deposit', methods=['GET', 'POST'])
def deposit():

    if 'id' not in session:
        return redirect('/login')

    info = request.args.get('info')

    if request.method == 'POST':

        try:

            amount = int(request.form.get('amount'))

            if amount <= 0:
                return redirect(
                    url_for(
                        'deposit',
                        info="Enter an amount greater than 0"
                    )
                )

        except (ValueError, TypeError):

            return redirect(
                url_for(
                    'deposit',
                    info="Enter the amount properly"
                )
            )

        data = get_data()
        users = data['users']

        for i in users:

            if i['id'] == session['id']:

                i['balance'] += amount

                time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

                i['history'].append({
                    "description": f"{amount} is deposited",
                    "time": time
                })

                update_data(data)

                return redirect(
                    url_for('checkbalance')
                )

    return render_template(
        'deposit.html',
        info=info
    )


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():

    if 'id' not in session:
        return redirect('/login')

    info = request.args.get('info')

    if request.method == 'POST':

        try:

            amount = int(request.form.get('amount'))

            if amount <= 0:
                return redirect(
                    url_for(
                        'withdraw',
                        info="Enter an amount greater than 0"
                    )
                )

        except (ValueError, TypeError):

            return redirect(
                url_for(
                    'withdraw',
                    info="Enter the amount properly"
                )
            )

        data = get_data()
        users = data['users']

        for i in users:

            if i['id'] == session['id']:

                if i['balance'] >= amount:

                    i['balance'] -= amount

                    time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

                    i['history'].append({
                        "description": f"{amount} is withdrawn",
                        "time": time
                    })

                    update_data(data)

                    return redirect(
                        url_for('checkbalance')
                    )

                else:

                    return render_template(
                        'withdraw.html',
                        info="Insufficient Balance"
                    )

    return render_template(
        'withdraw.html',
        info=info
    )


@app.route('/viewtransactions')
def viewtransactions():

    if 'id' not in session:
        return redirect('/login')

    data = get_data()
    users = data['users']

    for i in users:

        if i['id'] == session['id']:

            history = i['history']

            return render_template(
                'viewtransactions.html',
                history=history
            )

    return redirect('/login')


@app.route('/profile')
def profile():

    if 'id' not in session:
        return redirect('/login')

    data = get_data()
    users = data['users']

    for i in users:

        if i['id'] == session['id']:

            return render_template(
                'profile.html',
                user=i
            )

    return redirect('/login')

@app.route('/changepin', methods=['GET', 'POST'])
def changepin():

    if 'id' not in session:
        return redirect('/login')

    info = request.args.get('info')

    if request.method == 'POST':

        email = request.form.get('email')

        data = get_data()
        users = data['users']

        for i in users:

            if i['id'] == session['id']:

                if i['email'] == email:

                    username = i['name']

                    otp = generate_otp()

                    session['email'] = email
                    session['otp'] = otp

                    send_email(email, username, otp)

                    return redirect('/verify')

                else:
                    return redirect(
                        url_for('changepin',
                                info="Enter your registered email")
                    )

    return render_template('changepin.html', info=info)

if __name__ == "__main__":
    app.run(debug=True)

