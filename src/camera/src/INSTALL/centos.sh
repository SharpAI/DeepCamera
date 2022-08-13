#!/bin/bash
echo "========================================================="
echo "==!! Shinobi : The Open Source CCTV and NVR Solution !!=="
echo "========================================================="
echo "To answer yes type the letter (y) in lowercase and press ENTER."
echo "Default is no (N). Skip any components you already have or don't need."
echo "============="
if [ ! -e "./conf.json" ]; then
    cp conf.sample.json conf.json
fi
if [ ! -e "./super.json" ]; then
    echo "Default Superuser : admin@shinobi.video"
    echo "Default Password : admin"
    cp super.sample.json super.json
fi
echo "Shinobi - Run yum update"
sudo yum update -y
echo "Shinobi - Get dependencies"
#Install EPEL Repo
sudo yum install epel-release -y
#Enable Nux Dextop repo for FFMPEG
sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm
sudo yum install ffmpeg ffmpeg-devel -y
echo "Shinobi - Do you want to Install Node.js?"
echo "(y)es or (N)o"
read nodejsinstall
if [ "$nodejsinstall" = "y" ] || [ "$nodejsinstall" = "Y" ]; then
    sudo wget https://rpm.nodesource.com/setup_8.x
    sudo chmod +x setup_8.x
    ./setup_8.x
    sudo yum install nodejs -y
fi
echo "============="
echo "Shinobi - Do you want to use MariaDB or SQLite3?"
echo "SQLite3 is better for small installs"
echo "MariaDB (MySQL) is better for large installs"
echo "(S)QLite3 or (M)ariaDB?"
echo "Press [ENTER] for default (MariaDB)"
read sqliteormariadb
if [ "$sqliteormariadb" = "S" ] || [ "$sqliteormariadb" = "s" ]; then
    sudo npm install jsonfile
    sudo yum install -y sqlite sqlite-devel -y
    node ./tools/modifyConfiguration.js databaseType=sqlite3
    if [ ! -e "./shinobi.sqlite" ]; then
        echo "Creating shinobi.sqlite for SQLite3..."
        sudo cp sql/shinobi.sample.sqlite shinobi.sqlite
    else
        echo "shinobi.sqlite already exists. Continuing..."
    fi
else
    echo "============="
    echo "Shinobi - Do you want to Install MariaDB?"
    echo "(y)es or (N)o"
    read mysqlagree
    if [ "$mysqlagree" = "y" ] || [ "$mysqlagree" = "Y" ]; then
        sudo yum install mariadb mariadb-server -y
        #Start mysql and enable on boot
        sudo systemctl start mariadb
        sudo systemctl enable mariadb
        #Run mysql install
        sudo mysql_secure_installation
    fi
    echo "============="
    echo "Shinobi - Database Installation"
    echo "(y)es or (N)o"
    read mysqlagreeData
    if [ "$mysqlagreeData" = "y" ] || [ "$mysqlagreeData" = "Y" ]; then
        echo "What is your SQL Username?"
        read sqluser
        echo "What is your SQL Password?"
        read sqlpass
        sudo mysql -u $sqluser -p$sqlpass -e "source sql/user.sql" || true
        sudo mysql -u $sqluser -p$sqlpass -e "source sql/framework.sql" || true
        echo "Shinobi - Do you want to create a new user for viewing and managing cameras in Shinobi? You can do this later in the Superuser panel."
        echo "(y)es or (N)o"
        read mysqlDefaultData
        if [ "$mysqlDefaultData" = "y" ] || [ "$mysqlDefaultData" = "Y" ]; then
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
fi
echo "============="
echo "Shinobi - Install NPM Libraries"
sudo npm install
echo "============="
echo "Shinobi - Install PM2"
sudo npm install pm2 -g
echo "Shinobi - Finished"
sudo chmod -R 755 .
touch INSTALL/installed.txt
if [ "$mysqlDefaultData" = "y" ] || [ "$mysqlDefaultData" = "Y" ]; then
    echo "=====================================" > INSTALL/installed.txt
    echo "=======   Login Credentials   =======" >> INSTALL/installed.txt
    echo "|| Username : $userEmail" >> INSTALL/installed.txt
    echo "|| Password : $userPasswordPlain" >> INSTALL/installed.txt
    echo "|| API Key : $apiKey" >> INSTALL/installed.txt
    echo "=====================================" >> INSTALL/installed.txt
    echo "=====================================" >> INSTALL/installed.txt
fi
echo "Shinobi - Start Shinobi and set to start on boot?"
echo "(y)es or (N)o"
read startShinobi
if [ "$startShinobi" = "y" ] || [ "$startShinobi" = "Y" ]; then
    sudo pm2 start camera.js
    sudo pm2 start cron.js
    sudo pm2 startup
    sudo pm2 save
    sudo pm2 list
fi
if [ "$mysqlDefaultData" = "y" ] || [ "$mysqlDefaultData" = "Y" ]; then
    echo "details written to INSTALL/installed.txt"
    echo "====================================="
    echo "=======   Login Credentials   ======="
    echo "|| Username : $userEmail"
    echo "|| Password : $userPasswordPlain"
    echo "|| API Key : $apiKey"
    echo "====================================="
    echo "====================================="
fi
if [ ! "$sqliteormariadb" = "M" ] && [ ! "$sqliteormariadb" = "m" ]; then
    echo "====================================="
    echo "||=====   Install Completed   =====||"
    echo "====================================="
    echo "|| Login with the Superuser and create a new user!!"
    echo "||==================================="
    echo "|| Open http://$(ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p'):8080/super in your web browser."
    echo "||==================================="
    echo "|| Default Superuser : admin@shinobi.video"
    echo "|| Default Password : admin"
    echo "====================================="
    echo "====================================="
else
    echo "+=================================+"
    echo "||=====   Install Completed   =====||"
    echo "|| Access the main Shinobi panel at http://$(ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p'):8080 in your web browser."
    echo "+=================================+"
fi