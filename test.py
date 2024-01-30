from cloudpayments import CloudPayments


client = CloudPayments('pk_a2d44a7570fe7490cfe41bb85f660', 'b3185a124e9a9a4d80183156216221f8')
print(client.test())