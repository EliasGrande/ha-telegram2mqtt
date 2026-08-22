FROM eclipse-mosquitto:2.0

USER root
RUN apk add --no-cache openssl
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh
CMD ["/setup.sh"]
