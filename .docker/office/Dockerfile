FROM openjdk:25-bookworm
LABEL maintainer="ITK Development <itkdev@mkb.aarhus.dk>"

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get -y install \
  libreoffice-common \
  unoconv \
  hyphen-af hyphen-en-us \
  default-jre \
  libreoffice-java-common \
  fonts-dejavu fonts-dejavu-core fonts-dejavu-extra \
  fonts-droid-fallback fonts-dustin fonts-f500 fonts-fanwood fonts-freefont-ttf fonts-liberation \
  fonts-lmodern fonts-lyx fonts-sil-gentium fonts-texgyre fonts-tlwg-purisa fonts-opensymbol && \
  rm -rf /var/lib/apt/lists/*

EXPOSE 8100

ENTRYPOINT ["/usr/bin/libreoffice"]
CMD ["--headless", "--nologo", "--nofirststartwizard", "--accept=\"socket,host=0.0.0.0,port=8100;urp\""]
