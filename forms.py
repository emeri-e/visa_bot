from utils.form_fields import BaseForm, SelectField, CharField

class AvailabilityForm(BaseForm):
    category = SelectField(name='AppointmentCategoryId3', choices=['Premium', 'Normal'])
    location = SelectField(name='', choices=[])
    visa_type = SelectField(name='', choices=[])
    visa_subtype = SelectField(name='', choices=[])
    appointment_for = SelectField(name='AppointmentFor1', choices=['Family', 'Individual'])

    applicants_no = SelectField(name='ApplicantsNo1', required=False, choices=list(range(2,10)))


# AppointmentFor1: Family
# ApplicantsNo1: 4
# AppointmentFor3: Individual
# ApplicantsNo3: 
# Location3: 
# Mission3: 
# VisaType3: 
# VisaSubType3: 
# AppointmentFor2: Individual
# ApplicantsNo2: 
# Location2: 
# Mission2: 
# VisaType2: 
# VisaSubType2: 
# AppointmentFor5: Individual
# ApplicantsNo5: 
# Location5: 
# Mission5: 
# VisaType5: 
# VisaSubType5: 
# AppointmentCategoryId3: 5c2e8e01-796d-4347-95ae-0c95a9177b26
# Location1: 
# Mission1: 
# VisaType1: 
# VisaSubType1: 
# AppointmentCategoryId1: 
# AppointmentCategoryId4: 
# AppointmentFor4: Individual
# ApplicantsNo4: 
# AppointmentCategoryId5: 
# AppointmentCategoryId2: 
# Location4: 2ce8338d-3193-4301-8eb0-685ad7b90cfb
# Mission4: 
# VisaType4: 89c087ba-c645-4bfa-a6fc-749c5182eaf2
# VisaSubType4: 3498fe00-15e7-484d-afd0-dcce51b76b68
# CaptchaData: fTJ8C4H9SZMctxhXNFU/rXGtL7CdzINUjd2I3nEtNbPPlZPuInIbxArccOTEbdHJKAHlA/eTX7FdEpcxbATj5EZsADd9qTmrojP7ywjhRXAapWiQ9xgGvWcHoVTjToZU+uwWajEPIU+LoVXOGNBD91FN6YxwWPxlXr4DdO5hPWU=
# ScriptData: jo+WrPiNo78ZDGuNpLOXpEo5tcRburItrGNsaJgbsr2egGOWEvOhGb42RWKjpqnuYiDlM8j+EcDFQAvf+zFLdDHQAz3m3Jha4UwQdrnlnC9DAHR5fxAMB//VdIN+PwzyhzMsW6pb5ozFe4nMqZUFXljH23fL2ZvakwOTRTWkeKKoafErWlwXWIO3Oy6ehIKwGbZT3GIlJ1eA82nJOq7msJ6AjMRVoK875d+J3Xto173qUmuqcj7V4/zogU6//veuYHx5ZzD8KI/4xpa0SHbtf4d4xzLvGBMOTE87aiVECOw70UTnw1JjmruT4kHp3L7/hQQD4goySzwM4cpvdlitL0CJ1TYc50tADinHPsg5iBmiEtWQYn+zywtuOAsb90zc4Y66iDu1EkbK1tQlqN+Mqw==
# ResponseData: [{"Id":"VisaType4","Start":"2024-10-17T05:25:46.162Z","End":"2024-10-17T05:24:49.604Z","Total":2307,"Selected":false},{"Id":"Location4","Start":"2024-10-17T05:25:51.308Z","End":"2024-10-17T05:23:40.885Z","Total":2791,"Selected":false},{"Id":"ApplicantsNo1","Start":"2024-10-17T07:13:17.993Z","End":"2024-10-17T07:09:48.073Z","Total":2258,"Selected":false},{"Id":"AppointmentCategoryId3","Start":"2024-10-17T07:17:29.293Z","End":"2024-10-17T07:17:31.920Z","Total":2627,"Selected":true},{"Id":"VisaSubType4","Start":"2024-10-17T07:21:23.980Z","End":"2024-10-17T07:21:26.297Z","Total":2317,"Selected":true}]
# __RequestVerificationToken: CfDJ8FJkEUwVqCdNqgyhVtFmY8oijJNLVk9pL42qTl8dnpUtN_DfP6dBY_9A-t3V55n3lrmNkZjaorfC0eD8_EieKZyTsN9xh_CFc42jxlxMIoVmL7qCyza3ozOWCJrBnV0ybbnivsXcgxC_6eiw-Ds_Y6YEAJYRQJhRPUngHPngCj2_TZrDod7DVuHlxrdcZPUQ8Q
# X-Requested-With: XMLHttpRequest