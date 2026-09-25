package com.smarterp.shared.storage;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.DeleteBucketPolicyArgs;
import io.minio.GetBucketPolicyArgs;
import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import jakarta.annotation.PostConstruct;

import java.io.InputStream;

@Service
public class MinioService {

    private final MinioClient minioClient;
    private final String bucket;
    private final String baseUrl;

    public MinioService(
            @Value("${minio.endpoint:http://localhost:9000}") String endpoint,
            @Value("${minio.access-key:minioadmin}") String accessKey,
            @Value("${minio.secret-key}") String secretKey,
            @Value("${minio.bucket:applicant-cvs}") String bucket
    ) {
        this.minioClient = MinioClient.builder()
                .endpoint(endpoint)
                .credentials(accessKey, secretKey)
                .build();
        this.bucket = bucket;
        this.baseUrl = endpoint + "/" + bucket;
    }

    @PostConstruct
    public void ensureBucketAndPolicy() {
        try {
            boolean exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucket).build());
            if (!exists) {
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
            }

            // The bucket stays PRIVATE: CVs are personal data. The AI engine
            // downloads them with its own MinIO credentials (signed request).
            // Older versions of this service made the bucket public-read, so
            // remove any policy left behind.
            String policy;
            try {
                policy = minioClient.getBucketPolicy(GetBucketPolicyArgs.builder().bucket(bucket).build());
            } catch (io.minio.errors.ErrorResponseException e) {
                policy = null; // NoSuchBucketPolicy: already private
            }
            if (policy != null && !policy.isBlank()) {
                minioClient.deleteBucketPolicy(DeleteBucketPolicyArgs.builder().bucket(bucket).build());
            }
        } catch (Exception e) {
            throw new RuntimeException("Could not initialise the MinIO bucket: " + e.getMessage(), e);
        }
    }

    public String uploadCv(MultipartFile file, String objectName) {
        try (InputStream is = file.getInputStream()) {
            minioClient.putObject(
                    io.minio.PutObjectArgs.builder()
                            .bucket(bucket)
                            .object(objectName)
                            .stream(is, file.getSize(), -1)
                            .contentType(file.getContentType())
                            .build()
            );
            return baseUrl + "/" + objectName;
        } catch (Exception e) {
            throw new RuntimeException("Could not upload the CV: " + e.getMessage(), e);
        }
    }
}