import socket
import sys
import threading
from threading import Thread

cli_sockets = []
srv_sockets = []

TOTAL_THREAD = 20
NUM = 1
IMAGE_FILTER = "X"

def client_side(cur_clientsocket, IP_port):
	global NUM
	with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
		srv_sockets.append(s)
		# Client socket first receive waiting
		s_out = ""
		msg = cur_clientsocket.recv(1024)
		if msg != b"":
			
			
			# when msg is b'' , server's Client thread can detect client is terminated
			s_out += request_handler(msg, s, cur_clientsocket,IP_port)	
			if(s_out != ""):	
				s_out = (str(NUM) +"  [Conn:    "+ str(len(cli_sockets))+"/  " + str(TOTAL_THREAD)+"]\n" ) + s_out
				s_out+=("[CLI disconnected]\n")
				s_out+=("[SRV disconnected]\n")
				s_out+=("-----------------------------------------------")
				NUM+= 1
				print(s_out)
		cli_sockets.remove(cur_clientsocket)
		srv_sockets.remove(s)
		cur_clientsocket.close()
		s.close()
			
	

def request_handler(msg, s, cur_clientsocket, IP_port):
	global IMAGE_FILTER
	s_out = ""
	# when request comes
	if msg[0:3] != b"GET":
		return ""
	req_msg_list = msg.decode().split("\r\n\r\n",1)
	req_header = req_msg_list[0]
	req_header_list = req_header.split("\r\n")

	request_1_line = req_header_list[0].split(" ",2)
	request_2_line = req_header_list[2].split(":",1)[1]
	method = request_1_line[0]
	
	host = req_header_list[1].split(" ",1)[1]
	
	url_filter = "X"
	prev_request_1_line = []
	prev_request_1_line.append(request_1_line[0])
	prev_request_1_line.append(request_1_line[1])

	# yonsei 포함여부 확인
	if "yonsei" in host:
		host = "linuxhowtos.org"
		prev_request_1_line 
		request_1_line[1] = "http://" +host +"/" +request_1_line[1].split("/",3)[3]
		req_header_list[0] = " ".join(request_1_line)
		req_header_list[1] = "Host: "+host
		url_filter = "O"
	
	# image_on setting 
	for i in request_1_line[1].split("?"):
		if i == "image_on":
			IMAGE_FILTER = "X"
		elif i == "image_off":
			IMAGE_FILTER = "O"

	s_out += "[ "+url_filter+" ] URL filter | [ "+IMAGE_FILTER+" ] Image filter\n\n"
	s_out += ("[CLI connected to " + IP_port + "]\n")
	s_out += "[CLI ==> PRX --- SRV]"+ "\n"

	# Line 1 출력
	s_out += ("  > "+ prev_request_1_line[0] + " "+ prev_request_1_line[1] + "\n")
	# Line 2 출력
	s_out += ("  >"+ request_2_line + "\n") 

	s.connect((host, 80))
	s_out += ("[SRV connected to www."+ host+ ":80]"+ "\n") 
	s_out += ("[CLI --- PRX ==> SRV]"+ "\n")
	# Line 1 출력
	s_out += ("  > "+ request_1_line[0]+ " "+ request_1_line[1] + "\n" )
	# Line 2 출력
	s_out += ("  >"+ request_2_line + "\n") 
	
	for i in req_header_list:
		if i.split(":",1)[0] == "Connection":
			req_header_list.remove(i)
			req_header_list.append("Connection: close")
	
	msg = ("\r\n".join(req_header_list) +"\r\n\r\n" + req_msg_list[1]).encode()

	s.send(msg)

	res_list = []
	while True:
		received_msg = s.recv(65000)
		
		if not received_msg:
			break
		res_list.append(received_msg)
		
	res_header_list = (str(res_list[0]).split("\\r\\n\\r\\n")[0]).split("\\r\\n")
	status_code = res_header_list[0].split(" ",1)[1]
	
	s_out+=("[CLI --- PRX <== SRV]"+ "\n")
	s_out+=("  > "+status_code+ "\n")

	content_type ="?"
	content_length="0"
	for i in res_header_list:
		header_key = i.split(":",1)[0]
		if header_key == "Content-Type":
			content_type = i.split(":",1)[1]
		elif header_key == "Content-Length":	
			content_length = i.split(":",2)[1]
	
	if ((IMAGE_FILTER == "O") and (content_type.split("/")[0] == " image")) :
		real_content_length = " 0"
	else:
		real_content_length = content_length
	if status_code == "200 OK":
		s_out+=("  >"+ content_type + content_length + "bytes"+ "\n")
		s_out+=("[CLI <== PRX --- SRV]"+ "\n")
		s_out+=("  > "+status_code+ "\n")
		s_out+=("  >"+ content_type + real_content_length + "bytes"+ "\n")
	else:
		s_out += (status_code + "\n")
	for res_msg in res_list:
		if ((IMAGE_FILTER == "O") and (content_type.split("/")[0] == " image")) :
			cur_clientsocket.send(res_msg.split(b'\r\n\r\n',1)[0])
			break
		else:
			cur_clientsocket.send(res_msg)
	return(s_out)

	
	
	

def main_loop():	
	#get system argument in order to set host, port number
	
	port = int(sys.argv[1])


	# use 'with as' in order to guarntee socket exist
	with socket.socket() as serversocket:
		# Let server's socket bind in the host and port number, and listen upto 5
		serversocket.bind(("127.0.0.1", port))
		serversocket.listen(TOTAL_THREAD)
		print("Starting proxy server on port %d"%port)
		print("-----------------------------------------------")
		#Let server code can run forever
		while True:
			try:
				# because server socket can accept upto 5 connection so error handling for there are more than five connections
				if len(cli_sockets) <= TOTAL_THREAD:
					clientsocket ,addr = serversocket.accept()

					#IP_port variable is string variable for print IP:port number
					IP_port = addr[0]+ ":"+ str(addr[1])

					#in order to close all the socket when server terminate we maintain client socket array in global
					cli_sockets.append(clientsocket)

					# Thread for clinet generate
					chat_thread = Thread(target =client_side, args =(clientsocket, IP_port))
					chat_thread.setDaemon(True)
					chat_thread.start()

					# Print new client connection information on Server's terminal 
					
					# Print new client connection inforamtion on the other clients' terminals
					
			
			# Keyboard Interrupt ^C handling code
			except KeyboardInterrupt:
				for s in cli_sockets:
					s.close()
				for s in srv_sockets:
					s.close()
				serversocket.close()
				break

				
main_loop()