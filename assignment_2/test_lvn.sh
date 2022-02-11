# Test LVN
for f in ../examples/test/lvn/*.bril; do
    echo ${f}
    BEFORE=`bril2json < ${f} | brili -p 2>&1 | head -n 1`
    AFTER=`bril2json < ${f} | python3 lvn.py | brili -p 2>&1 | head -n 1`
    if [ $BEFORE -ne $AFTER ]; then
        echo "Running " ${f} " -- " "FAIL";
    else
        echo "Running " ${f} " -- " "PASSED";
    fi
done
