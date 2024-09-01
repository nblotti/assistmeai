# Use the official httpd image as a parent image
FROM httpd:latest

# Create a necessary directory for apache logs
RUN mkdir -p /var/log/apache2 && \
    chown www-data:www-data /var/log/apache2



# Copy the virtual host configuration
COPY vhost.conf /usr/local/apache2/conf/extra/httpd-vhosts.conf

COPY vhost_ssl.conf /usr/local/apache2/conf/extra/httpd-ssl.conf

# Copy custom httpd.conf to the correct location
COPY httpd.conf /usr/local/apache2/conf/httpd.conf


# Installing OpenSSH server on top of the httpd image
RUN apt-get update && \
    apt-get install -y openssh-server && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure OpenSSH
RUN mkdir /var/run/sshd && \
    echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/Port 22/Port 2222/' /etc/ssh/sshd_config && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDgEwwEzNNuUQPpe4ahtle/yJZ+5/Vr0WNu53JcBncsoYwDWIrtQqPuTCpby/pd9/grM130bpstGbA6Pnj0swBx0FdepRgI6HsM/di5tiQq5ewVpJe0yQXEx+7jHMfT89x/iuen8zWOE0lSF1+zglX/Zg0bsZ8C007KzTjGcVN5mrt5mNeC6HR6Ui4CYLUpQK4s6xJvTk/I1+E6dcCnqoXUOyDJAeD6yXjcyjmPHm6Y+WizYGEwvL2LYQwqHivVXWy8G/pKZUnmNe1ijH8j01j687tDBdkRg+rk8Dc7jTGdXrUs6ABCWPZFg0gY0A9CgBWfNHUBinfgVDApy+FHnbUgzLr5+BixtQmcE+mPjeI6pvO94tGGxzV1F5HBo//cuDaAzBxz7coAz7dcRD+tzaH7ssLOfBJME3oblKczqK5MarXkgZICOTLJ9EekzwNTYC1+9F3//sHxc3G6GfW4wdNWXaabpkmhpUwcqDHe6GmV8QFfcHV/DaCAqcp3Rgmgiztv3N2dwyiCOildV5fiyWJmpgarJUoTSSwnlVs44FxUXb//+YOLWfprHIshFn6XZtg+Wz7PkMPDw5F9G1RN2RcO7FSewSNeTxfIq3yeOffdqvzhY6Dx8S9hQRFA0ifR0fWDnl1+ICkgdCa6c2ODkjUMs22m/QfQd5Z/fbLmDNM3w== /home/nblotti/.ssh/id_rsa' >> /root/.ssh/authorized_keys && \
    chmod 600 /root/.ssh/authorized_keys

# Expose ports 80 (HTTP), 443 (HTTPS), and 2222 (SSH)
EXPOSE 80 443 2222

# Start Apache and SSH in the foreground
CMD ["sh", "-c", "service ssh start && httpd-foreground"]