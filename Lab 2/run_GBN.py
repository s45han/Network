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

buffer_size=4

def run_simulation():
    global buffer_size,event_list,buffer_size,current_sending_slot
    global receiver_RN,length_buffer,sequence_buffer,time_buffer, current_time
    global NEXT_EXPECTED_FRAME,receiver_RN
    #init empty buffer for length, seq numbers and time
    length_buffer=create_empty_buffer(buffer_size,frame_length)
    sequence_buffer=create_empty_buffer(buffer_size,None,False)
    time_buffer=create_empty_buffer(buffer_size)
    
    sequence_buffer[0]=0
    length_buffer[0]=frame_length
    
    #init param
    event_list=[]
    num_success=0
    current_sending_slot=0
    current_time=0
    
    #receiver side
    NEXT_EXPECTED_FRAME=0
    receiver_RN=0

    while num_success<required_num_success:

        if len(event_list)==0:
            sender_send_process() 
            
        while len(event_list)>0 and num_success<required_num_success:
            # print("reading new packet----------------------------"+str(len(event_list)))+"----------------------------"+str(current_time)
            event_list=sorted(event_list,key=lambda event:event["time"] )
            event=event_list[0]            
            # print event_list
            # print current_sending_slot            
            
            if current_time< event["time"]:
                #update current time if all packet is sent
                if sequence_buffer[buffer_size-1]!=None:
                    current_time=event["time"]
                else:                
                    #keep sending if not all packet in buf is sent
                    sender_send_process()
                
            
            elif event["type"]=="TIMEOUT":   
                #all pkt in buffer need to be resent, clear the event list

                #check if all packets ack are slides, if so we need to get the new sequence number 
                k=0
                while k<buffer_size:
                    temp_seq_num=sequence_buffer[k]
                    if temp_seq_num!=None:
                        new_seq_number=temp_seq_num
                    else:
                        break
                    k+=1                
                length_buffer=create_empty_buffer(buffer_size,frame_length)
                sequence_buffer=create_empty_buffer(buffer_size,None,False)
                time_buffer=create_empty_buffer(buffer_size)
                sequence_buffer[0]=new_seq_number
                event_list=[]
                current_sending_slot=0
                sender_send_process()
            
            else: #ACK PACKET
                if event["status"]=="NO_ERROR" :
                    # print "4"
                    if event["sequence_num"] == sequence_buffer[0]:
                        #the first lost is not acked correctly: ignore
                        event_list.remove(event)
                        
                    elif (event["sequence_num"]-1)%(buffer_size+1) in sequence_buffer:
                        #remove the timeout for the acked packet
                        event_list.remove(event)

                        #make sure there is only one timeout
                        i=0
                        while i <len(event_list):
                            temp_event=event_list[i]
                            if temp_event["type"]=="TIMEOUT":
                                event_list.remove(temp_event)
                                # break
                            i+=1
                        
                        #slide the window by seq-P
                        num_to_slide=(event["sequence_num"]-sequence_buffer[0])%(buffer_size+1)                        
                        slide_window(num_to_slide)
                        num_success+=num_to_slide

                        # update next sending slot 
                        current_sending_slot=(current_sending_slot-num_to_slide)%(buffer_size)
                        
                    else: #packet is not acked correctly. 
                        event_list.remove(event)   

                else: #error or wrong sequence number, ignore
                     event_list.remove(event)
                     

            # print "number success=======================" +str(num_success)

        # return throughput               
        throughput=num_success*data_length*8/current_time
        return throughput



def slide_window(num_to_slide):
    global sequence_buffer, length_buffer, time_buffer, buffer_size

    i=0
    j=num_to_slide
    #check if all packets ack are slides, if so we need to get the new sequence number 
    # by getting the last sent seq num
    k=0
    while k<buffer_size:
        temp_seq_num=sequence_buffer[k]
        if temp_seq_num!=None:
            new_seq_number=temp_seq_num
        else:
            break
        k+=1

    #shift packets
    while i <(buffer_size-num_to_slide):
        sequence_buffer[i]=sequence_buffer[j]
        length_buffer[i]=length_buffer[j]
        time_buffer[i]=time_buffer[j]
        i+=1
        j+=1

    #set not yet txed packet to none
    i=num_to_slide
    while i >0:
        sequence_buffer[buffer_size-i]=None
        length_buffer[buffer_size-i]=None
        time_buffer[buffer_size-i]=None
        i-=1

    # update new timeout if there is still packet not received
    if sequence_buffer[0] is not None:
        event_list.append({"type":"TIMEOUT","time":time_buffer[0]+TIMEOUT,"sequence_num":sequence_buffer[0]})
    else:
        sequence_buffer[0]=new_seq_number
    

def create_empty_buffer(N,value=None,incrementing=False):
    i=0
    empty_buffer=[]

    while i<N:
        empty_buffer.append(value)
        if incrementing==True:
            value+=1
        i+=1
    return empty_buffer


def sender_send_process():
    global current_time, event_list,trans_rate,length_buffer,current_sending_slot,sequence_buffer,frame_length
    # print "in sending process"
    # print current_sending_slot
    
    # add length in buffer
    length_buffer[current_sending_slot]=frame_length
    
    #update current time after trans delay   
    current_time+=(length_buffer[current_sending_slot]*8)/float(trans_rate)
    
    #get the sequence number to send 
    if current_sending_slot==0:        
        seq_number_to_send=sequence_buffer[0]
    else:
        seq_number_to_send=(sequence_buffer[current_sending_slot-1]+1)%(buffer_size+1)
        sequence_buffer[current_sending_slot]=seq_number_to_send
    
    time_buffer[current_sending_slot]=current_time

    
    
    #add timeout only if there is none
    i=0
    timeout_exist=False
    while i<len(event_list):
        event=event_list[i]
        if event["type"]=="TIMEOUT":
            timeout_exist=True
            break
        i+=1
    if timeout_exist==False:        
        pkt_timeout_time=current_time+TIMEOUT
        event_list.append({"type":"TIMEOUT","time":pkt_timeout_time,"sequence_num":seq_number_to_send})
   
    #pass through forward and reverse channel, see results
    send_result=send(sequence_buffer[current_sending_slot],current_time)

    #update the current sending slot after previous one is sent
    current_sending_slot=(current_sending_slot+1)%(buffer_size)

   
    if send_result is not None:
        #add the event to list if not lost
        event_list.append(send_result)

    
   
    

def send(sn,cur_time):
    global receiver_RN,NEXT_EXPECTED_FRAME,prop_delay,trans_rate,header
    
    ######################forward channel
    #generate status code: lost, error, no_error
    forward_status=generate_error_event(frame_length*8)
    if forward_status=="LOST":
        return None
    
    #prop delay
    cur_time+=2*prop_delay
    
    #trans delay for ACK
    cur_time+=header*8/float(trans_rate)
    
    #####################receiver
    #ACK, check SN with RN add to event list
    if sn==NEXT_EXPECTED_FRAME and forward_status=="NO_ERROR":
        #updated next expected if matches        
        NEXT_EXPECTED_FRAME=(NEXT_EXPECTED_FRAME+1)%(buffer_size+1)
       
    receiver_RN=NEXT_EXPECTED_FRAME    
    ACK_event={"type":"ACK","status":forward_status,"sequence_num":receiver_RN}


    ######################reverse channel
    #generate status code: lost, error, no_error
    reverse_status=generate_error_event(header*8)

    if reverse_status=="LOST":
        return None
    else:
        ACK_event["time"]=cur_time
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
    i=0
    j=0

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
    
    while i<5:
        result[0][i]+=result[1][i]
        i+=1
    final= result[0]
    generate_csv(final)

def generate_csv(result):
    type="GBN"
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

