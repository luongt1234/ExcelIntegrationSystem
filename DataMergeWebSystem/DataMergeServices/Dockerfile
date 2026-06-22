FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj files and restore dependencies
COPY ["DataMerge.API/DataMerge.API.csproj", "DataMerge.API/"]
COPY ["DataMerge.Application/DataMerge.Application.csproj", "DataMerge.Application/"]
COPY ["DataMerge.Domain/DataMerge.Domain.csproj", "DataMerge.Domain/"]
COPY ["DataMerge.Infrastructure/DataMerge.Infrastructure.csproj", "DataMerge.Infrastructure/"]
RUN dotnet restore "DataMerge.API/DataMerge.API.csproj"

# Copy the rest of the code and build
COPY . .
WORKDIR "/src/DataMerge.API"
RUN dotnet build "DataMerge.API.csproj" -c Release -o /app/build

# Publish
FROM build AS publish
RUN dotnet publish "DataMerge.API.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Final stage/image
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .

# Expose port
EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080

ENTRYPOINT ["dotnet", "DataMerge.API.dll"]
