#Add to crontab for automation schedule execution. In this case the time set is every 5 minutes.
#*/5 *  * * *    root    sh /$PATH/autorestartsvc.sh -2>> /var/log/autorestartsvc.log

#LOG Path
#/var/log/autorestartsvc.log

#Variable execute application status verification command
a=$(netstat -tunlp | grep nginx)

#Variable timestemp from the log
date=$(date +%d/%m/%Y":"%H:%M:%S)

# Repeat loop counter variable
c=1

# Print text on screen
echo "$data | Checking if the NGINX is up!"

# condition iteration
if [ "$a" ] #check if the return is true
then
         echo "$data | Status [Active]: $a" #true displays port | process
else
         echo "$data | Status:[DOWN] \n$data | Executing start command" #false starts loop
         #start loop while $c < 3 then do
         while [ $c -le 3 ]
         of
                #command action restart
                systemctl restart nginx
               

                #Wait 3 sec to start the scan
                sleep 3
               
                # Check if the service is up
                b=$(netstat -tunlp | grep nginx)

                # Validate if it is the expected return
                if [ -n "$b" ]
                then
                        # If true print the output
                        echo "$data | Status [Active] : $b"
                        c=$(($c + 5))
                 else
                         # If false print the output
                         echo "$data | Performing $c of 3 Attempts"
                         c=$(($c + 1))

                 fi
         #close loop
         done
#end iteration
fi
