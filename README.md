# 🚨 LureBuster - Anti-Phishing Flood | Endpoint Stress Test
![Python](https://img.shields.io/badge/python-3.12.7-blue.svg) ![Matplotlib](https://img.shields.io/badge/matplotlib-3.10.3-red.svg)  ![license](https://img.shields.io/badge/license-apache%202.0-yellow.svg)  

Designed to combat phishing by flooding scam sites with deceptive data, LureBuster's configurable traffic engine also serves as a tool for teams to test their own endpoints against high-volume requests.

![image](https://github.com/user-attachments/assets/a733b5d9-ef4a-4553-aeb2-aac5d2a14103)

## 🎯 Features  
- **Data Flood**: Generates a huge amount of data
- **Random Data**: Mimics real user data using [Faker](https://github.com/joke2k/faker)
- **Parametrized Data**: Dynamically change payloads, using predefined placeholders
  - Example: 'Her first name is **{{PERSON_first_name_female}}**, and her last name is **{{PERSON_last_name_female}}**'
  - Result: 'Her first name is **Michelle**, and her last name is **Gardner**'
  - Internally this will call Faker's [Providers](https://faker.readthedocs.io/en/stable/providers.html) methods.
- **Multi-Threaded**: Concurrent request engine
- **JSON Templates**: Save/load attack profiles
- **Metrics**: Check realtime requests per second, error rates, attack duration, successful requests

## Can be used for:
### 🛡️**Anti-Phishing**:  
  - Generate fake data at scale
  - Mimic organic user data patterns
  - Degrades phishing database utility

### 🧪**Endpoint Testing**:  
  - Multi-threaded load simulation  
  - Custom payload injection  
  - Performance metric collection
  - Stress test 

## 🛡️ Compliance Note
This tool is designed for:
- Authorized security testing (with permission)
- Ethical phishing disruption (targeting confirmed scam sites)
- Legitimate load testing of owned infrastructure
  
⚠️ *Never test systems without explicit authorization.*

## 🐱 Code Reviews by Haxi  
Our Chief Meowker Officer ensures:  
- Readable, maintainable code  
- No hairball-inducing complexity  
- Bug-free merges (when not napping on the keyboard)  

<img src="https://github.com/user-attachments/assets/f982ff07-b030-4e07-be9d-cc3eb8509f59" width="400">

