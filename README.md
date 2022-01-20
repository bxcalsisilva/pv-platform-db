# pv-platform-db
The database population for PV Platform project

## SQL
- Tables creation (db-create.sql)
- Configuration (db-initiate.sql)


## [Database Diagram]

![DB Diagram](/db-diagram.png)

## AWS
### EC2 Connection

Connection:
- Linux
```
ssh -i <ssh-key-directory> ubuntu@ec2-18-228-196-113.sa-east-1.compute.amazonaws.com
```
- Windows
1. Download Putty https://www.putty.org/
2. Under Category, select Session and copy ip address: `ubuntu@ec2-18-228-196-113.sa-east-1.compute.amazonaws.com`
3. Under Category, in Connection expand SSH and select Auth. Browse for .ppk (ssh-key) file
4. Go back to Session, add Name of session under Saved Sessions, e.g. putty-aws, and Save
	- Allows to load the previous steps for next sessions
5. Select saved session and Open

### RDS Connection

```
# Requires EC2 Login
mysql -u admin -ppvplatform -h pv-db.ckzi7vlatwr4.sa-east-1.rds.amazonaws.com -P 3306
```

#### Considerations
- hourly process may output unnecesary performance evaluations.
	- Output already cut to only retrieve cleaned data.
- Unreliable values in daily process may display as Nan with No in respective Ok column.
