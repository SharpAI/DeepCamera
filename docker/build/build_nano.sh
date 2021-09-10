
cd tensorflow
./build_nano.sh
cd ../
docker-compose -f docker-compose-arm64v8.yml build
