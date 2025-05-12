import pickle
from fastapi import FastAPI
from apis_models.default_model import Request
from sqlalchemy import create_engine
import pandas as pd
from typing import List

# ———————————————————————————————————————————————————————————————————————————————————————————————————————————
# Определение справочных данных (словари, значения, подключения, моделька)
engine = create_engine('sqlite:///DataBase', echo=False)
sup_dict_contact = {
    "Month-to-month": 3875,
    "One year": 1472,
    "Two year": 1685
}
sup_dict_payment = {
    "Electronic check": 2365,
    "Mailed check": 1604,
    "Bank transfer (automatic)": 1542,
    "Credit card (automatic)": 1521
}
mean_charges = 64

with open('clas_model.pkl', 'rb') as file:
    cls_model = pickle.load(file)

# Инициализация АПИ
app = FastAPI()


# ———————————————————————————————————————————————————————————————————————————————————————————————————————————
# Получение и предобработка данных
def data_preprocessing(type, item: Request):
    if type == 'conn':
        df = pd.read_sql('Select * from temp_data', con=engine, index_col='index')
    else:
        # Преобразование данных в нужный формат
        req_DICT = {
            "gender": item.gender,
            "age": item.age,
            "tenure": item.tenure,
            "partner": item.partner,
            "dependents": item.dependents,
            "adv_PhoneService": 0,
            "adv_MultipleLines": 0,
            "adv_InternetService": 0,
            "adv_OnlineSecurity": 0,
            "adv_OnlineBackup": 0,
            "adv_DeviceProtection": 0,
            "adv_TechSupport": 0,
            "adv_StreamingTV": 0,
            "adv_StreamingMovies": 0,
            "adv_Contract": sup_dict_contact.get(item.contract, 0),  # с обработкой отсутствия значения
            "adv_PaperlessBilling": item.paperless_billing,  # исправлено имя поля
            "adv_paymentMethod": sup_dict_payment.get(item.payment_method, 0),  # исправлено имя поля
            "MonthlyCharges": item.monthlyCharges,
            "TotalCharges": 0,
            "big_sped_new_person": (1 if (item.tenure < 15) and (item.monthlyCharges > 64) else 0),
            "one_service_count": (item.monthlyCharges / len(item.services))
        }

        # Создание DataFrame
        df = pd.DataFrame([req_DICT])

        # Отметка выбранных услуг
        for service in item.services:
            if service in df.columns:
                df[service] = 1

    return df


# ———————————————————————————————————————————————————————————————————————————————————————————————————————————
# Сохранение данных вместе с предсказанием от модельки
def save_data(item: Request):
    df = data_preprocessing('req', item)
    clf_df = df[
        ['adv_PaperlessBilling', 'adv_Contract', 'adv_paymentMethod', 'tenure', 'MonthlyCharges', 'TotalCharges',
         'big_sped_new_person', 'one_service_count']]

    # Предсказание и сохранение
    result = cls_model.predict(clf_df)
    df['adv_Churn'] = result
    df.to_sql('temp_data', con=engine, if_exists='append')


# ———————————————————————————————————————————————————————————————————————————————————————————————————————————
# Дообучение модельки
def training():
    df = data_preprocessing('conn', None)

    if df['adv_Churn'].count() > 500:
        print('Lets train!')

        cls_model = cls_model.fit(df.drop('adv_Churn', axis=1), df['adv_Churn'])

        with open('clas_model.pkl', 'wb') as file:
            pickle.dump(cls_model, file)

        return 1
    else:
        print('Need more data')
        return 0


# ———————————————————————————————————————————————————————————————————————————————————————————————————————————
# Первый роут для сохранения данных
@app.post('/save_request/')
# http://127.0.0.0:8000/save_request/
async def save_request(request: Request):
    try:
        save_data(request)
    except Exception as e:
        print(f'Some error: {e}')


# ———————————————————————————————————————————————————————————————————————————————————————————————————————————
# Первый роут для сохранения данных
@app.get('/train_model/')
# http://127.0.0.0:8000/train_model/
async def train_model():
    try:
        res = training()
        return res
    except Exception as e:
        print(f'Error: {e}')


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",  # Доступ с любого IP
        port=8000,  # Порт по умолчанию
    )
