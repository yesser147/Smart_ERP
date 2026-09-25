# ---- build: compile the Spring Boot jar ----
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build
# dependencies first, so they are cached when only the code changes
COPY pom.xml .
RUN mvn -B -q dependency:go-offline || true
COPY src ./src
RUN mvn -B -q -DskipTests package

# ---- run: small Java runtime image ----
FROM eclipse-temurin:21-jre
WORKDIR /app
RUN useradd --system --uid 1001 spring
COPY --from=build /build/target/smart-erp-core-0.0.1-SNAPSHOT.jar app.jar
USER spring
EXPOSE 8080
# secrets come from backend/.env through docker-compose (never baked into the image)
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
