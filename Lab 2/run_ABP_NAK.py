#!/usr/bin/python
import sys
import random,math, numbers,decimal,datetime

#parameters
header=54 #bytes
data_length=1500 #bytes
trans_rate=5000000 #Mb/s
BER=0
required_num_success=1000
frame_length=header+data_length
prop_delay=0.005
TIMEOUT=prop_delay*2.5


def run_simulation():
    global sender_SN, receiver_RN, NEXT_EXPECTED_FRAME,NEXT_EXPECTED_ACK
    global frame_length, event_list, current_time, trans_rate,required_num_success
    num_success=0
    current_time=0
    event_list=[]
    timeout_list=[]
    
    #sender 
    sender_SN=0
    NEXT_EXPECTED_ACK=1

    #receiver
    receiver_RN=0
    NEXT_EXPECTED_FRAME=0
    sender_send_process()
    
    while len(event_list)>0 and num_success<required_num_success: 
        event_list=sorted(event_list,key=lambda event:event["time"] )        
        # print event_list
        event=event_list[0]
        # print event
        
        ### TIMEOUT PACKET
        if event["type"]=="TIMEOUT":            
            if event["sequence_num"]==sender_SN:
                #resend pkt, clear event list
                current_time=event['time']
                event_list=[]
                sender_send_process()                
            else:
                event_list.remove(event_list[0])    
                print("shouldn't be here when timeout have wrong seq number")

        ### ACK PACKET
        else:
            if current_time<event['time']:
                    current_time=event['time']
            if event["type"]=="NAK":
                event_list=[]
                # print sender_SN
                sender_SN=event['sequence_num']
                # print sender_SN
                NEXT_EXPECTED_ACK=(sender_SN+1)%2
                sender_send_process()
            else:
                if event["status"]=="NO_ERROR" and event["sequence_num"]==NEXT_EXPECTED_ACK:
                    
                    #check to remove the timeout packet
                    timeout_event=event_list[1]
                    if timeout_event["type"]=="TIMEOUT" and timeout_event["sequence_num"]==sender_SN:
                        event_list.remove(timeout_event)
                    else:
                        print("should be a timeout event after ack")
                    
                    #ncrement counter (sn,expected), updated num_success before sending 
                    NEXT_EXPECTED_ACK=(NEXT_EXPECTED_ACK+1)%2
                    sender_SN=(sender_SN+1)%2
                    num_success+=1
                    if num_success==required_num_success:
                        break                                          
                    #send new packet
                    event_list=[]
                    sender_send_process()

                else:#not equal expected number or has error    
                    #do nothing, waiting for timeout
                    event_list.remove(event)    
        # print "==============================="+str(num_success)
    
    
    throughput=num_success*data_length*8/current_time
    return throughput

def sender_send_process():
    # print"sending"+str(sender_SN)
    global current_time, event_list,sender_SN,trans_rate,frame_length
    #update current time and get packet timeout 
    current_time+=frame_length*8/float(trans_rate) 
    pkt_timeout_time=current_time+TIMEOUT    
    #add timeout event to list
    event_list.append({"type":"TIMEOUT","time":pkt_timeout_time,"sequence_num":sender_SN})
    
    #send packet to receiver
    send_result=send(sender_SN,current_time)
    
    if send_result is not None:
        #add the ack event to list if not lost
        event_list.append(send_result)
    
    

def send(sn,cur_time):
    global receiver_RN,NEXT_EXPECTED_FRAME,prop_delay,trans_rate,header 
    
    ######################forward channel
    #generate status code: lost, error, no_error
    forward_status=generate_error_event(frame_length*8)
    if forward_status=="LOST":
        return None

    cur_time+=2*prop_delay
    

    #####################receiver:
    # ACK, check SN with RN add to event list
    # update next expected frame number
    # print forward_status
    if sn==NEXT_EXPECTED_FRAME and forward_status=="NO_ERROR":
        NEXT_EXPECTED_FRAME=(NEXT_EXPECTED_FRAME+1)%2
        ack_type="ACK"
    else:
        ack_type="NAK"
        # print sn
        # print NEXT_EXPECTED_FRAME
    receiver_RN=NEXT_EXPECTED_FRAME    
    
    ACK_event={"type":ack_type,"status":forward_status,"sequence_num":receiver_RN}
    #ack trans delay
    cur_time+=header*8/float(trans_rate)
    
    ######################reverse channel
    #generate status code: lost, error, no_error
    ACK_event["time"]=cur_time
    reverse_status=generate_error_event(header*8)

    if reverse_status=="LOST":
        return None
    else:
        if forward_status=="NO_ERROR" and reverse_status=="NO_ERROR":
            ACK_event["status"]="NO_ERROR"
        else:
            ACK_event["status"]="ERROR"
        return ACK_event


def generate_error_event(iteration):
    global frame_length,BER
    error_result=0
    i=0
    # iteration=frame_length*8
    while i<iteration:
        generated=random.random()
        if generated<=BER:
            error_result+=1
        i+=1
    if error_result==0:
        result= "NO_ERROR"
    elif error_result>=5:
        result= "LOST" 
    else:
        result= "ERROR"
    return result



def set_simulation_param():
    global BER,prop_delay,TIMEOUT

    result=[]
    # run with different parameters
    for prop in [0.005, 0.25]:
        prop_delay=prop
        result2=[]
        row=[]
        for timeout in [2.5, 5, 7.5, 10, 12.5]:
            timeoutresult=[]
            row1=""
            TIMEOUT=prop_delay*timeout
            for ber in [0,0.00001,0.0001]:
                BER=ber            
                throughput=run_simulation()
                print throughput
                timeoutresult.append(throughput)
                row1+=str(throughput)+","            
            row.append(row1)
        result.append(row)
    i=0
    # append result of different prop delay
    while i<5:
        result[0][i]+=result[1][i]
        i+=1
    final= result[0]
    generate_csv(final)

def generate_csv(result):
    # print result to csv
    type="ABP_NAK"
    now=datetime.datetime.now()
    time=str(now.month) + "_" + str(now.day)+"_"+str(now.hour) +"_"+ str(now.minute) 
    filename=type+".csv"
    f=open(filename,"w+")
    for line in result:
        print line
        f.write(line+"\n")
    f.close()

if __name__ == "__main__":

    set_simulation_param()
    
