name1="my_screen"  
path="/home/pi"
screen -dmS $name1
screen -x -S $name1 -p 0 -X stuff "python $path/AS3935.py > $path/AS3935_output \n" 
screen -x -S $name1 -p 0 -X stuff "y\n" 
sleep 10
screen -x -S $name1 -p 0 -X stuff "y\n" 
