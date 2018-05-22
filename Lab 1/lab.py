#!/usr/bin/python
import sys
import random,math, numbers,decimal,datetime

#global variables
#k,p,lambda, a
c=1000000
l=12000
t=5000

#variables that store the performance metrics
infinite_report=[]
finite_Ploss_report=[]
combined_En_report=[]


def generate_random(): 
    
    global observer_list,arrival_list
    global sorted_combined
    global p,k,lam,a,service_time
    num_arrival=0 #number of arrival events
    num_observer=0 #number of arrival events

    arrival_sum=0
    observer_sum=0
    #list of generated observers and arrivals

    observer_list=[]
    arrival_list = []

    #calculate and update lambda, a
    lam=c*p/float(l)    
    a=3*lam
    service_time=l/float(c)

    # For debug
    # print "service_time: "+str(service_time)
    # print "t: "+str(t)
    # print "k: "+str(k)
    # print "c: "+str(c)
    # print "l: "+str(l)
    # print "p: "+str(p)
    # print "1/lambda: "+str(1/float(lam))
    # print "lambda: "+str(lam)
    # print "a: "+str(a)
    print "---------------------------------------------"
    
    exp_sum=0    
    test_list=[] #used for variance

    # generta arrival list
    while arrival_sum<=t:        
        
        indiv_num =(-1)*math.log(1- random.random())/lam
        arrival_sum+=indiv_num    
        
        if arrival_sum>t:
            arrival_sum-=indiv_num
            break
        arrival_list.append(['arrival',arrival_sum]) 
        num_arrival += 1
        test_list.append(indiv_num) 
    
    
    # calculate expectation
    expectation = arrival_sum / num_arrival
    # print "Expectation: " + str(expectation)
    
    #calcualte variance 
    j=0
    differenceSquare = 0
    for arrival in test_list:    
        differenceSquare += math.pow((arrival - expectation),2)
        j += 1
    variance = differenceSquare / num_arrival
    # print "Variance:   " + str(variance)

    

    # generate observer list with alpha
    while observer_sum<=t:
    
        indiv_num = random.random()        
        observer_sum+=(-1)*math.log(1- random.uniform(0,1))/a
        
        if observer_sum>t:
            break

        observer_list.append(['observer',observer_sum]) 
        num_observer += 1
        
    
    #combines observer and arrivals
    combined= observer_list+arrival_list
    observer_list=observer_list

    #sort combined list based on event time
    sorted_combined= sorted(combined,key=lambda event:event[1] )
    

def start_simulation(report_type):
    
    global finite_Ploss_report, infinite_report, combined_En_report,finite_col_num,comb_col_num
    
    #generate arrival and observer list
    generate_random()


    # init measurement
    num_arrival=0
    num_departure=0
    num_observer=0
    idle_counter=0
    num_dropped=0

    last_depature_time=0
    num_inqueue=0
    num_inqueue_sum=0
    record_list=[]
    departure_list=[]
    time_lastevent=0
    time_idle=0

    for event in sorted_combined:            
        
        #check all not dispatched departure. 
        #if time is smaller than event time, then departure event is record and then removed
        for depart in departure_list:    
            if depart[1]<=event[1]:
                num_inqueue-=1
                if num_inqueue==0:                
                    time_lastevent=depart[1]
                
                num_departure+=1                
                departure_list.remove(depart)    
                # print depart
                # print num_inqueue
            else:
                break
            
        # arrival event    
        if event[0]=='arrival':
            # print event

            num_arrival+=1

            if num_inqueue==0:     
                last_depature_time=event[1]+service_time
                time_idle+=event[1]-time_lastevent
                # print "current idle time: "+str(event[1]-time_lastevent)
                time_lastevent=event[1]

            elif num_inqueue<k:
                last_depature_time+=service_time
                
            elif num_inqueue>=k: #queue full need to drop
                num_dropped+=1
                continue

            #increment num in queue and reset wait time    
            num_inqueue+=1    
            
            #insert new depature into depature list
            if last_depature_time<=t:        
                departure_list.append(['departure',last_depature_time])
                # print ['departure',last_depature_time]
            

        # observer event 
        elif event[0]=='observer':
            num_observer+=1
            if num_inqueue==0:
                idle_counter+=1
            
            num_inqueue_sum+=num_inqueue
            
            
            #current_queue_occupancy, num_arrival, num_depart,num_obser, idle_counter, num_dropped
            # record=['observer',event[1],num_inqueue,num_arrival,num_departure,num_observer,idle_counter,num_dropped]
            # print record

    #calculate performance metrics
    avg_queue_num=num_inqueue_sum/float(num_observer)
    p_idle=time_idle/float(t)*100
    p_loss=num_dropped/float(len(arrival_list))*100

    print "E[N]  for p="+str(p)+", k= "+str(k)+": "+str(avg_queue_num)
    if is_finite==False:
        print "Pidle for p="+str(p)+", k= "+str(k)+": "+str(p_idle)+"%"
    else:
        print "Ploss for p="+str(p)+", k= "+str(k)+": "+str(p_loss)+"%"
        

    #store results into report variables
    if report_type=="infinite_report":
        infinite_report.append([p,avg_queue_num,p_idle])
    elif report_type=="finite_Ploss_report":
        finite_Ploss_report[finite_col_num].append(p_loss)
    elif report_type=="combined_En_report":
        combined_En_report[comb_col_num].append(avg_queue_num)

def set_sim_variables():
    global p,k,lam,a,service_time,is_finite
    global finite_Ploss_report, infinite_report, combined_En_report,finite_col_num,comb_col_num

    #INFINITE queue 
    if is_finite==False: 
        
        ################################################
        ###Question 3 for 0.25<p<0.95
        infinite_report.append(["rho","E[N]","Pidle"])
        p_list=[]
        p_value=0.25        
        while p_value<=0.95:            
            p_list.append(p_value)
            p_value=round(p_value+0.1,2)
            
        
        ###Question 4 for p=1.2
        p_value=1.2
        p_list.append(p_value)

        for p_value    in p_list:
            p=p_value
            start_simulation("infinite_report")
        

        generate_report("infinite_report",infinite_report)


    #FINITE queue
    else:    
        ################################################
        ###Question 6.1: 0.5<p<1.

        #report header
        combined_En_report.append(["rho","K=5","K=10","K=40","Infinite"])
        
        k_list = [5,10,40,float('inf')]
        p_list=[]
        p_value=0.5
        while p_value<=1.5:

            p_list.append(p_value)
            p_value =round(p_value+0.1,1)

        comb_col_num=1
        for p_value    in p_list:
            p=p_value            
            combined_En_report.insert(comb_col_num,[p_value])
            for k_value     in k_list:                
                k=k_value
                start_simulation("combined_En_report")
            comb_col_num+=1
        
        generate_report("combined_En_report",combined_En_report)


        ################################################
        ##Question 6.2: 0.4<p<10
        
        finite_Ploss_report.append(["rho","K=5","K=10","K=40"])

        p_list2=[]        
        p_value =0.4
        while p_value<2:                
            p_list2.append(p_value)
            p_value=round(p_value+0.1,1)

        while p_value<5:                
            p_list2.append(p_value)
            p_value=round(p_value+0.2,1)
        
        while p_value<=10.2:                

            p_list2.append(p_value)
            p_value=round(p_value+0.4,1)

        k_list = [5,10,40]

        # print p_list2
        # print k_list
        finite_col_num=1
        for p_value    in p_list2:
            p=p_value
            
            finite_Ploss_report.insert(finite_col_num,[p_value])
            for k_value     in k_list:            
                k=k_value
                start_simulation("finite_Ploss_report")
            finite_col_num+=1

        # print finite_Ploss_report
        generate_report("finite_Ploss_report",finite_Ploss_report)
        
#output result to excel
def generate_report(type,report):
    now=datetime.datetime.now()
    time=str(now.month) + "_" + str(now.day)+"_"+str(now.hour) +"_"+ str(now.minute) 
    filename=type+"_"+time+".csv"
    f=open(filename,"w+")
    for line in report:
        row=", ".join( str(e) for e in line )+"\n"
        f.write(row)
    f.close()
 

def check_type():
    global k,is_finite
    
    if len(sys.argv) == 1:
        print_cmd_errors()
        exit()
    else:
        try:
            #check what type of simulation to run: finite or infinite
            if sys.argv[1].lower()=="finite":                            
                is_finite=True
            elif sys.argv[1].lower()=='infinite':            
                k=float('inf')
                is_finite=False
        except:
            print_cmd_errors()

def print_cmd_errors():
    print "ERROR! Please pass in valid agrumenets"
    print "\n--->Usage: lab.py infinite OR lab.py finite \n"
    # sys.exit()


if __name__ == "__main__":
    
    check_type() #check if run finite or infinite queue simulation 
    set_sim_variables() #start whole simulation process
