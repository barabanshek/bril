# Test DCE on tests
for f in ../examples/test/tdce/*.bril; do
    BEFORE=`bril2json < ${f} | brili -p 2>&1 | head -n 1`
    AFTER=`bril2json < ${f} | python3 dce.py | brili -p 2>&1 | head -n 1`
    if [ $BEFORE -ne $AFTER ]; then
        echo "Running " ${f} " -- " "FAIL";
    else
        echo "Running " ${f} " -- " "PASSED";
    fi
done
