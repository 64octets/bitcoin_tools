from utils.utils import decode_utxo, change_endianness
from json import loads, dumps

# Input and output files
fin = open('./data/utxos.txt', 'r')
fout = open('./data/non-std.txt', 'w+')

types = [0, 1, 2, 3, 4, 5]
starts = ["5121", "5141", "5221", "5241"]
for line in fin:
    data = loads(line[:-1])
    utxo = decode_utxo(data["value"])

    for out in utxo.get("outs"):
        if out.get("out_type") not in types:
            s = out.get("data")[:4]
            if s not in starts:
                result = {"tx_id": change_endianness(data["key"][2:])}
                result.update(out)
                fout.write(dumps(result) + '\n')

