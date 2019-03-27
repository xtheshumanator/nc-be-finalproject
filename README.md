# SecureSoniCryptor (SSC) Back End

This is the back end API service for the SecureSoniCryptor; a secure file sharing app that uses audio to encrypt file.

To see what APIs are supported click [here](https://ssc-be.herokuapp.com/).

## Getting Started

### Prerequisites

The following are required to use the app:
1. Python 3.7 with pip and Pycharm (or another appropriate alternative IDE).
2. AWS S3 account (the key and secret): this will be used to create workspaces and save encrypted files in workspaces. As long as the keys (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) are in your environment variables, the AWS library will use this.
3. ACR account (the key and secret): this will be used to get the audio metadata which will be used for the audio analysis. See the acrconfig.py file for the data you'll need from your ACR account. 
4. Postgres for the database.

### Installing

#### Get the code

Fork the project from git. Then copy the git url and in the appropriate folder on your machine:

```
git clone <url from git>
```
This will create the project on your local machine. Open the project in your chose IDE.

#### Setup the app locally
In the terminal, run the following to install the necessary packages:
```
 pip install -r requirements.txt
```

To install the database:
_It is wise to comment out the inserts so fresh data is added as you use the system._
```
 psql -f setup.sql
```

#### Run the app locally
Right click on server.py then click on create (right below the debug) to setup the environment variables; this is where you'd add the ACR config and your AWS config (if you're not saving this in an aws file). 

Check out the instructions of the [front end ](https://github.com/theshumanator/nc-fe-finalproject) to kick it off so the back end can be tested.