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

RUNS = 30

PARAM = str(sys.argv[1]).replace(" ", "_").replace("%", "")

def log_stats(times_list, protocol):
    confidence = 0.95
    mean = sum(times_list) / len(times_list)
    std_err = scipy.stats.sem(times_list)
    ci = scipy.stats.t.interval(
        confidence, len(times_list) - 1, loc=mean, scale=std_err
    )
    print(f"Mean: {mean}")
    print(f"Confidence interval: {ci}")

    # Append the stats to the file
    with open("stats.txt", "a") as f:
        f.write(f"{PARAM} {protocol} Mean: {mean}\n")
        f.write(f"{PARAM} {protocol} Confidence interval: {ci}\n")


tcp_times = []
udp_times = []
for i in range(1, RUNS + 1):
    print(f"Run {PARAM} {i}")
    start = time.time()
    tcp_client.main()
    end = time.time()
    print(f"TCP time {PARAM} {i}: {end - start}")
    tcp_times.append(end - start)

    start = time.time()
    udp_client.main()
    end = time.time()
    print(f"UDP time {PARAM} {i}: {end - start}")
    udp_times.append(end - start)

log_stats(tcp_times, "TCP")
log_stats(udp_times, "UDP")

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
plt.yticks(np.arange(y_min, y_max, 5))
plt.xlabel("Run Number")
plt.ylabel("Time")
plt.legend()
plt.title("TCP and UDP Times with Means")
plt.savefig(f"graphs/time_run_mean_{PARAM}.png")
