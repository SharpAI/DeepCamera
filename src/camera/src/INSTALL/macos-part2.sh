
#!/bin/bash
echo "========================================================="
echo "==!! Shinobi : The Open Source CCTV and NVR Solution !!=="
echo "=================== Mac OS Install Part 2 ==============="
echo "========================================================="
echo "Shinobi - Database Installation"
echo "(y)es or (N)o"
read mysqlagreeData
if [ "$mysqlagreeData" = "y" ]; then
    echo "Shinobi - Use root for database installation?"
    echo "(y)es or (N)o"
    echo "What is your SQL Username?"
    read sqluser
    echo "What is your SQL Password?"
    read sqlpass
    echo "You may now be asked for your Administator (root for Mac OS, not MySQL) password"
    sudo mysql -u $sqluser -p$sqlpass -e "source sql/user.sql" || true
    sudo mysql -u $sqluser -p$sqlpass -e "source sql/framework.sql" || true
    echo "Shinobi - Do you want to create a new user for viewing and managing cameras in Shinobi? You can do this later in the Superuser panel."
    echo "(y)es or (N)o"
    read mysqlDefaultData
    if [ "$mysqlDefaultData" = "y" ]; then
        escapeReplaceQuote='\\"'
        groupKey=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 7 | head -n 1)
        userID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 6 | head -n 1)
        userEmail=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 6 | head -n 1)"@"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 6 | head -n 1)".com"
        userPasswordPlain=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 6 | head -n 1)
        userPasswordMD5=$(echo   -n   "$userPasswordPlain" | md5sum | awk '{print $1}')
        userDetails='{"days":"10"}'
        userDetails=$(echo "$userDetails" | sed -e 's/"/'$escapeReplaceQuote'/g')
        echo $userDetailsNew
        apiIP='0.0.0.0'
        apiKey=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
        apiDetails='{"auth_socket":"1","get_monitors":"1","control_monitors":"1","get_logs":"1","watch_stream":"1","watch_snapshot":"1","watch_videos":"1","delete_videos":"1"}'
        apiDetails=$(echo "$apiDetails" | sed -e 's/"/'$escapeReplaceQuote'/g')
        rm sql/default_user.sql || true
        echo "USE ccio;INSERT INTO Users (\`ke\`,\`uid\`,\`auth\`,\`mail\`,\`pass\`,\`details\`) VALUES (\"$groupKey\",\"$userID\",\"$apiKey\",\"$userEmail\",\"$userPasswordMD5\",\"$userDetails\");INSERT INTO API (\`code\`,\`ke\`,\`uid\`,\`ip\`,\`details\`) VALUES (\"$apiKey\",\"$groupKey\",\"$userID\",\"$apiIP\",\"$apiDetails\");" > "sql/default_user.sql"
        sudo mysql -u $sqluser -p$sqlpass --database ccio -e "source sql/default_user.sql" > "INSTALL/log.txt"
        echo "The following details will be shown again at the end of the installation."
        echo "====================================="
        echo "=======   Login Credentials   ======="
        echo "|| Username : $userEmail"
        echo "|| Password : $userPasswordPlain"
        echo "|| API Key : $apiKey"
        echo "====================================="
        echo "====================================="
        echo "** To change these settings login to either to the Superuser panel or login to the dashboard as the user that was just created and open the Settings window. **"
    fi
fi
echo "============="
echo "Shinobi - Install NPM Libraries"
sudo npm install
echo "============="
echo "Shinobi - Install PM2"
sudo npm install pm2 -g
if [ ! -e "./conf.json" ]; then
    sudo cp conf.sample.json conf.json
fi
if [ ! -e "./super.json" ]; then
    echo "Default Superuser : admin@shinobi.video"
    echo "Default Password : admin"
    sudo cp super.sample.json super.json
fi
echo "Shinobi - Finished"
touch INSTALL/installed.txt
sudo chmod -R 755 .
echo "=====================================" > INSTALL/installed.txt
echo "=======   Login Credentials   =======" >> INSTALL/installed.txt
echo "|| Username : $userEmail" >> INSTALL/installed.txt
echo "|| Password : $userPasswordPlain" >> INSTALL/installed.txt
echo "|| API Key : $apiKey" >> INSTALL/installed.txt
echo "=====================================" >> INSTALL/installed.txt
echo "=====================================" >> INSTALL/installed.txt
echo "Shinobi - Start Shinobi and set to start on boot?"
echo "(y)es or (N)o"
read startShinobi
if [ "$startShinobi" = "y" ]; then
    sudo pm2 start camera.js
    sudo pm2 start cron.js
    sudo pm2 startup
    sudo pm2 save
    sudo pm2 list
fi
echo "details written to INSTALL/installed.txt"
echo "====================================="
echo "=======   Login Credentials   ======="
echo "|| Username : $userEmail"
echo "|| Password : $userPasswordPlain"
echo "|| API Key : $apiKey"
echo "====================================="
echo "====================================="