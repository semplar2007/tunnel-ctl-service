import paramiko
import xml.etree.ElementTree as ET

print ('Connecting to SSH...')
ssh = paramiko.SSHClient()
try:
    # auto-accepting host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('semplar.net', username='testuser', password='testpass')
    
    print ('Running ls -l...')
    stdin, stdout, stderr = ssh.exec_command('ls -l')
    print (''.join(stdout.readlines()))
    
    print ('Reading XML file')
    stdin, stdout, stderr = ssh.exec_command('cat /var/www/default/example.xml')
    et = ET.parse(stdout).getroot()
    print (ET.tostring(et))
    print ('Root element: ' + et.tag)
    print ('Root element childs: ' + str(len(et)))
    
    print ('Trying apt-get')
    stdin, stdout, stderr = ssh.exec_command('apt-get install paramiko')
    print ('Return code: ' + str(stdout.channel.recv_exit_status()))
    
    print ('Trying apt-cache')
    stdin, stdout, stderr = ssh.exec_command('apt-cache search paramiko')
    print ('Return code: ' + str(stdout.channel.recv_exit_status()))
    
finally:
    try: ssh.close()
    except: pass
print ('Done with SSH...')

print ()

# trying linode
from linode.api import Api

print ('Connecting to Linode...')
# c = Api('hvq1qgE2NPV2MCXFgita5uR2DRJ1TxLONbkryGUEAs4Ea6j5aMOMx0q8R3ToZuy1') # semplar.net API key
c = Api('fQXt9hhePJhp759JdCPxVfEpg7o99IBDUNreCISGNd8GSFdzJfSnGWCwdmiCEF55')
try:
    print ('API response: ' + str(c.test.echo(giveback = 1)))
finally:
    pass # api is RESTful
print('Done with Linode')
