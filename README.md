# Block-Chain
I've always been interested in blockchain technology and the potential that it has as a secure, anonymous ledger. This technology has had a large impact on the world of tech and will continue to revolutionize the way we process and look at transactions. 

My opinion has always been that the best way to learn a new technology is to make and implement it yourself, so I figured I would use python to develop a functional blockchain.

This blockchain can coordinate chains between multiple machines/virtual environments/ conatiners. Individual chain instances coordinate using HTTP GET and POST requests and allow the chains to mine blocks, add transactions, register nodes and reach consensus. The default rule is that the longest, valid chain is authoritative.

# Docker
This blockchain program can be run in a Docker container. To build the repo in a local docker container, you can follow the instructions below:
1. Clone repository
2. Build docker container-> $ docker build -t block-chain
3. Run container-> $ docker run --rm -p 80:5000 block-chain
4. Add instances using the sommand above with variations in the public port number (81:5000, 82:5000, etc)
