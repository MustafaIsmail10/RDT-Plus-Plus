"""
Main experimentation script. Should run on client side.

First start servers on same container
Manually clear rules and introduce new delay, loss, etc. param

1. Loop 1..30
2.  Run tcp_client send protocol
3. loop 1..30
4.  Run udp_client send protocol
5. Graph time vs run number graph and save to file.

"""
import client_tcp as tcp_client
import client_udp as udp_client
import time
import scipy.stats
import matplotlib.pyplot as plt
import os
import numpy as np
import sys
import csv
import threading
import pickle


PARAM = str(sys.argv[1]).replace(" ", "_").replace("%", "")

if len(sys.argv) > 2:
    RUNS = int(sys.argv[2])
else:
    RUNS = 30

def log_stats(udp_times, tcp_times):
    confidence = 0.95
    mean_tcp = sum(tcp_times) / len(tcp_times)
    std = scipy.stats.sem(tcp_times)
    ci_tcp = scipy.stats.t.interval(
        confidence, len(tcp_times) - 1, loc=mean_tcp, scale=std
    )
    print("TCP")
    print(f"Mean: {mean_tcp}")
    print(f"Confidence interval: {ci_tcp}")
    
    mean_udp = sum(udp_times) / len(udp_times)
    std = scipy.stats.sem(udp_times)
    ci_udp = scipy.stats.t.interval(
        confidence, len(udp_times) - 1, loc=mean_udp, scale=std
    )
    print("UDP")
    print(f"Mean: {mean_udp}")
    print(f"Confidence interval: {ci_udp}")
    
    if not os.path.exists('stats.csv'):
        with open('stats.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["experiment", "tcp mean", "tcp ci", "udp mean", "udp ci"])

    with open('stats.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow([PARAM, mean_tcp, ci_tcp, mean_udp, ci_udp])
        writer.writerow([PARAM, f"{mean_tcp:.2f}", f"({ci_tcp[0]:.2f}, {ci_tcp[1]:.2f})", f"{mean_udp:.2f}", f"({ci_udp[0]:.2f}, {ci_udp[1]:.2f})"])
    
# tcp_times = []
# udp_times = []

if os.path.exists(f'udp_times_{PARAM}.pkl'):
    with open(f'lists/udp_times_{PARAM}.pkl', 'rb') as f:
        udp_times = pickle.load(f)
else:
    udp_times = []

if os.path.exists(f'tcp_times_{PARAM}.pkl'):
    with open(f'lists/tcp_times_{PARAM}.pkl', 'rb') as f:
        tcp_times = pickle.load(f)
else:
    tcp_times = []

if len(udp_times) == RUNS and len(tcp_times) == RUNS:
    print("Already ran.")
    sys.exit(0)

if len(udp_times) < RUNS:
    udp_times = []
    for i in range(1, RUNS + 1):
        print(f"Run {PARAM} {i}")
        
        # UDP
        start = time.time()
        udp_client.main()
        end = time.time()
        print(f"UDP time {PARAM} {i}: {end - start}")
        udp_times.append(end - start)
        
    with open(f'lists/udp_times_{PARAM}.pkl', 'wb') as f:
        pickle.dump(udp_times, f)

if len(tcp_times) < RUNS:
    tcp_times = []
    for i in range(1, RUNS + 1):
        # TCP
        start = time.time()
        tcp_client.main()
        end = time.time()
        print(f"TCP time {PARAM} {i}: {end - start}")
        tcp_times.append(end - start)
        
    with open(f'lists/tcp_times_{PARAM}.pkl', 'wb') as f:
        pickle.dump(tcp_times, f)

# print("Logging...")
# log_stats(tcp_times, "TCP")
# log_stats(udp_times, "UDP")
log_stats(udp_times, tcp_times)

# Plot the graph (ORIGINAL)
plt.figure()
plt.plot(range(1, len(tcp_times) + 1), tcp_times, label="TCP")
plt.plot(range(1, len(udp_times) + 1), udp_times, label="UDP")
plt.xticks(range(1, len(tcp_times) + 1))
y_min = min(min(tcp_times), min(udp_times))  # minimum y value
y_max = max(max(tcp_times), max(udp_times))  # maximum y value
plt.yticks(np.arange(y_min, y_max, 5))
plt.xlabel("Run Number")
plt.ylabel("Time")
plt.legend()
plt.title("TCP and UDP Times")
if not os.path.exists("graphs"):
    os.makedirs("graphs")
plt.savefig(f"graphs/time_run_{PARAM}.png")

# Calculate the means
tcp_mean = sum(tcp_times) / len(tcp_times)
udp_mean = sum(udp_times) / len(udp_times)

# # Plot the graph (WITH MEAN LINE)
plt.figure()
plt.plot(range(1, len(tcp_times) + 1), tcp_times, label="TCP")
plt.plot(range(1, len(udp_times) + 1), udp_times, label="UDP")
plt.axhline(y=tcp_mean, color='b', linestyle='--', label="TCP Mean")
plt.axhline(y=udp_mean, color='red', linestyle='--', label="UDP Mean")
plt.xticks(range(1, len(tcp_times) + 1))
y_min = min(min(tcp_times), min(udp_times))  # minimum y value
y_max = max(max(tcp_times), max(udp_times))  # maximum y value
plt.yticks(np.arange(y_min, y_max, 10))
plt.xlabel("Run Number")
plt.ylabel("Time")
plt.legend()
plt.title("TCP and UDP Times with Means")
plt.savefig(f"graphs2/time_run_mean_{PARAM}.png")


'''
# def run_udp(i):
#     start = time.time()
#     udp_client.main()
#     end = time.time()
#     print(f"UDP time {PARAM} {i}: {end - start}")
#     udp_times.append(end - start)

# def run_tcp(i):
#     start = time.time()
#     tcp_client.main()
#     end = time.time()
#     print(f"TCP time {PARAM} {i}: {end - start}")
#     tcp_times.append(end - start)

# for i in range(1, RUNS + 1):
#     print(f"Run {PARAM} {i}")
    
#     # UDP
#     udp_thread = threading.Thread(target=run_udp, args=(i,))
#     udp_thread.start()

#     # TCP
#     tcp_thread = threading.Thread(target=run_tcp, args=(i,))
#     tcp_thread.start()

#     # Wait for both threads to finish
#     udp_thread.join()
#     tcp_thread.join()
'''