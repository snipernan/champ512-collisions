/* File adapter for the official CHAMP-512 CryptHash function.
 * Contains no hash algorithm, matrix arithmetic, certificates or expected digest.
 * Build this file together with the unmodified official .c and .h files.
 */
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "CryptHash_AlgorithmInstance.h"

int main(int argc, char **argv)
{
    char *end;
    unsigned long long nbits, required;
    unsigned char *data;
    unsigned char output[80];
    FILE *input;
    long length;
    int code;

    if (argc != 3) {
        fprintf(stderr, "Usage: %s FILE MEANINGFUL_BITS\n", argv[0]);
        return 2;
    }
    for (const char *p = argv[2]; *p; ++p) {
        if (*p < '0' || *p > '9') {
            fprintf(stderr, "MEANINGFUL_BITS must be a positive decimal integer\n");
            return 2;
        }
    }
    errno = 0;
    nbits = strtoull(argv[2], &end, 10);
    if (errno || end == argv[2] || *end || nbits == 0) {
        fprintf(stderr, "Invalid meaningful bit length\n");
        return 2;
    }
    required = nbits / 8 + (nbits % 8 != 0);
    if (required > SIZE_MAX || required > LONG_MAX) {
        fprintf(stderr, "Input too large for this file adapter\n");
        return 2;
    }
    input = fopen(argv[1], "rb");
    if (!input) {
        perror(argv[1]);
        return 1;
    }
    if (fseek(input, 0, SEEK_END) != 0 || (length = ftell(input)) < 0 ||
        fseek(input, 0, SEEK_SET) != 0) {
        fprintf(stderr, "Could not determine file size\n");
        fclose(input);
        return 1;
    }
    if ((unsigned long long)length != required) {
        fprintf(stderr, "File size %ld does not match ceil(%llu/8) = %llu\n",
                length, nbits, required);
        fclose(input);
        return 2;
    }
    data = malloc((size_t)required);
    if (!data) {
        perror("allocate input");
        fclose(input);
        return 1;
    }
    if (fread(data, 1, (size_t)required, input) != (size_t)required) {
        fprintf(stderr, "Could not read complete input\n");
        fclose(input);
        free(data);
        return 1;
    }
    if (fclose(input) != 0) {
        perror("close input");
        free(data);
        return 1;
    }
    memset(output, 0xa5, sizeof(output));
    code = CryptHash(512, data, nbits, output);
    free(data);
    if (code != 0) {
        fprintf(stderr, "Official CryptHash returned %d\n", code);
        return 1;
    }
    for (size_t i = 64; i < sizeof(output); ++i) {
        if (output[i] != 0xa5) {
            fprintf(stderr, "Digest output guard changed\n");
            return 1;
        }
    }
    for (size_t i = 0; i < 64; ++i) printf("%02x", output[i]);
    putchar('\n');
    return ferror(stdout) ? 1 : 0;
}
