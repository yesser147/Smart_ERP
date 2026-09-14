package com.smarterp.shared.storage;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.SetBucketPolicyArgs;
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
    private final String publicBaseUrl;

    public MinioService(
            @Value("${minio.endpoint:http://localhost:9000}") String endpoint,
            @Value("${minio.access-key:minioadmin}") String accessKey,
            @Value("${minio.secret-key:minioadmin123}") String secretKey,
            @Value("${minio.bucket:applicant-cvs}") String bucket
    ) {
        this.minioClient = MinioClient.builder()
                .endpoint(endpoint)
                .credentials(accessKey, secretKey)
                .build();
        this.bucket = bucket;
        this.publicBaseUrl = endpoint + "/" + bucket;
    }

    @PostConstruct
    public void ensureBucketAndPolicy() {
        try {
            boolean exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucket).build());
            if (!exists) {
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
            }

            // Public-read policy: the ai_engine's process-cv step downloads
            // the PDF via a plain, unauthenticated GET request. Without
            // this, MinIO's default private bucket returns 403, which is
            // what turns into the "Échec de l'extraction du PDF" error
            // shown in the CV manager.
            String policy = """
                {
                  "Version": "2012-10-17",
                  "Statement": [
                    {
                      "Effect": "Allow",
                      "Principal": {"AWS": ["*"]},
                      "Action": ["s3:GetObject"],
                      "Resource": ["arn:aws:s3:::%s/*"]
                    }
                  ]
                }
                """.formatted(bucket);

            minioClient.setBucketPolicy(
                    SetBucketPolicyArgs.builder().bucket(bucket).config(policy).build()
            );
        } catch (Exception e) {
            throw new RuntimeException("Échec de l'initialisation du bucket MinIO: " + e.getMessage(), e);
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
            return publicBaseUrl + "/" + objectName;
        } catch (Exception e) {
            throw new RuntimeException("Échec de l'upload du CV: " + e.getMessage(), e);
        }
    }
}