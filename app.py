from flask import Flask, render_template, request, redirect, url_for, flash
from web3 import Web3
import web3
from web3.exceptions import ContractLogicError
import json, re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

with open('abi.json', 'r') as f:
    abi = json.load(f)

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
w3.middleware_onion.inject(web3.middleware.geth_poa.geth_poa_middleware, layer=0)

main_address = Web3.to_checksum_address("0x3df0d3d1c811fe61f560cdf034a65d26e80a1a20")
user_address = ""

for item in w3.eth.accounts:
    if item != main_address:
        w3.geth.personal.lock_account(item)
        break

contract_address = Web3.to_checksum_address("0x145e9b1Bff2bdD3e64954eb27F46e8F7B0E20a30")
contract = w3.eth.contract(contract_address, abi=abi)

def is_strong_password(password):
    if len(password) < 12:
        return "Пароль должен быть не менее 12 символов"
    if not re.search(r'[A-Z]', password):
        return "Пароль должен содержать хотя бы одну заглавную букву"
    if not re.search(r'[a-z]', password):
        return "Пароль должен содержать хотя бы одну строчную букву"
    if not re.search(r'\d', password):
        return "Пароль должен содержать хотя бы одну цифру"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Пароль должен содержать хотя бы один специальный символ"
    common_patterns = ["password", "123456", "123456789", "qwerty", "abc123", "password1", "qwerty123"]
    for pattern in common_patterns:
        if pattern in password.lower():
            return "Пароль не должен следовать простым шаблонам, таким как 'password123' или 'qwerty123'"
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global user_address
    if request.method == 'POST':
        address = request.form['address']
        password = request.form['password']
        try:
            address_checksum = Web3.to_checksum_address(address)
            w3.geth.personal.unlock_account(address_checksum, password)
            user_address = address_checksum
            flash('Успешный вход!', 'success')
            return redirect(url_for('menu'))
        except Exception as e:
            flash(f'Неверный адрес или пароль: {e}', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    global user_address
    if request.method == 'POST':
        password = request.form['password']
        password_error = is_strong_password(password)
        if password_error:
            flash(password_error, 'danger')
        else:
            address = w3.geth.personal.new_account(password)
            user_address = Web3.to_checksum_address(address)
            flash(f'Регистрация успешна! Ваш ключ: {address}', 'success')
            return redirect(url_for('menu'))
    return render_template('register.html')

@app.route('/menu')
def menu():
    if user_address == '':
        return redirect(url_for('index'))
    return render_template('menu.html')

@app.route('/logout')
def logout():
    global user_address
    if user_address == '':
        return redirect(url_for('index'))
    if user_address and user_address != main_address:
        w3.geth.personal.lock_account(user_address)
    user_address = ""
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('index'))

@app.route('/add_estate', methods=['GET', 'POST'])
def add_estate():
    if user_address == '':
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        number = request.form['number']
        address_info = request.form['address']
        estate_type = request.form['type']
        area = request.form['area']
        try:
            contract.functions.AddEstate(name, int(number), address_info, estate_type, int(area)).transact({'from': user_address})
            flash('Недвижимость добавлена успешно!', 'success')
        except ContractLogicError as e:
            flash(f'Ошибка контракта: {e.message}', 'danger')
        except ValueError:
            flash('Ошибка: неверный формат данных', 'danger')
    return render_template('add_estate.html')

@app.route('/add_advert', methods=['GET', 'POST'])
def add_advert():
    if request.method == 'POST':
        estate_id = request.form['estate_id']
        price = request.form['price']
        currency = request.form['currency']
        try:
            contract.functions.AddAdvert(int(estate_id), int(price), currency).transact({'from': user_address})
            flash('Объявление добавлено успешно!', 'success')
        except ContractLogicError as e:
            flash(f'Ошибка контракта: {e.message}', 'danger')
        except ValueError:
            flash('Ошибка: неверный формат данных', 'danger')
    return render_template('add_advert.html')

@app.route('/change_estate_status', methods=['GET', 'POST'])
def change_estate_status():
    if request.method == 'POST':
        estate_id = request.form['estate_id']
        try:
            contract.functions.ChangeEstateStatus(int(estate_id)).transact({'from': user_address})
            flash('Статус недвижимости изменен успешно!', 'success')
        except ContractLogicError as e:
            flash(f'Ошибка контракта: {e.message}', 'danger')
        except ValueError:
            flash('Ошибка: неверный формат данных', 'danger')
    return render_template('change_estate_status.html')

@app.route('/change_advert_status', methods=['GET', 'POST'])
def change_advert_status():
    if request.method == 'POST':
        estate_id = request.form['estate_id']
        try:
            contract.functions.ChangeAdvertStatus(int(estate_id)).transact({'from': user_address})
            flash('Статус объявления изменен успешно!', 'success')
        except ContractLogicError as e:
            flash(f'Ошибка контракта: {e.message}', 'danger')
        except ValueError:
            flash('Ошибка: неверный формат данных', 'danger')
    return render_template('change_advert_status.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        amount = request.form['amount']
        currency = request.form['currency']
        try:
            contract.functions.withdraw(int(amount), currency).transact({'from': user_address})
            flash('Средства выведены успешно!', 'success')
        except ContractLogicError as e:
            flash(f'Ошибка контракта: {e.message}', 'danger')
        except ValueError:
            flash('Ошибка: неверный формат данных', 'danger')
    return render_template('withdraw.html')

@app.route('/get_balance')
def get_balance():
    try:
        balance = contract.functions.get_balance().call({'from': user_address})
        flash(f'Ваш баланс: {balance}', 'success')
    except ContractLogicError as e:
        flash(f'Ошибка контракта: {e.message}', 'danger')
    return redirect(url_for('menu'))

@app.route('/get_estates')
def get_estates():
    try:
        estates = contract.functions.get_estates().call()
        return render_template('estates.html', estates=estates)
    except ContractLogicError as e:
        flash(f'Ошибка контракта: {e.message}', 'danger')
        return redirect(url_for('menu'))

@app.route('/get_adverts')
def get_adverts():
    try:
        adverts = contract.functions.get_adverts().call()
        return render_template('adverts.html', adverts=adverts)
    except ContractLogicError as e:
        flash(f'Ошибка контракта: {e.message}', 'danger')
        return redirect(url_for('menu'))

@app.route('/buy_estate', methods=['GET', 'POST'])
def buy_estate():
    if request.method == 'POST':
        estate_id = request.form['estate_id']
        value = request.form['value']
        try:
            contract.functions.buy_estate(int(estate_id)).transact({'from': user_address, 'value': int(value)})
            flash('Недвижимость успешно куплена!', 'success')
        except ContractLogicError as e:
            flash(f'Ошибка контракта: {e.message}', 'danger')
        except ValueError:
            flash('Ошибка: неверный формат данных', 'danger')
    return render_template('buy_estate.html')

if __name__ == '__main__':
    app.run(debug=True)
