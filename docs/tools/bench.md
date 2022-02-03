Benchmarks
==========

The `bench` directory in the Bril repository contains a fledgling suite of microbenchmarks that you can use to measure the impact of your optimizations.
(Benchmarks are different from tests because they are meant to actually calculate something instead of just exercising a language feature.)

The current benchmarks are:

* `ackermann`: Print the value of `Ack(m, n)`, the [two-argument Ackermann–Péter function][ackermann].
* `adler32`: Computes the [Adler-32 Checksum][adler32] of an integer array.
* `armstrong`: Determines if the input is an [Armstrong number][armstrong], a number that is the sum of its own digits each raised to the power of the number of digits.
* `check-primes`: Check the first *n* natural numbers for primality, printing out a 1 if the number is prime and a 0 if it's not.
* `collatz`: Print the [Collatz][collatz] sequence starting at *n*. Note: it is not known whether this will terminate for all *n*.
* `digial-root`: Computes the digital root of the input number.
* `eight-queens`: Counts the number of solutions for *n* queens problem, a generalization of [Eight queens puzzle][eight_queens].
* `euclid`: Calculates the greatest common divisor between two large numbers using the [Euclidean Algorithm][euclid] with a helper function for the modulo operator.
* `factors`: Print the factors of the *n* using the [trial division][trialdivision] method.
* `fib`: Calculate the *n*th Fibonacci number by allocating and filling an [array](../lang/memory.md) of numbers up to that point.
* `fizz-buzz`: The infamous [programming test][fizzbuzz].
* `gcd`: Calculate Greatest Common Divisor (GCD) of two input positive integer using [Euclidean algorithm][euclidean_into].
* `loopfact`: Compute *n!* imperatively using a loop.
* `mat-inv` : Calculates the inverse of a 3x3 matrix and prints it out.
* `mat-mul`: Multiplies two `nxn` matrices using the [naive][matmul] matrix multiplication algorithm. The matrices are randomly generated using a [linear congruential generator][rng].
* `newton`: Calculate the square root of 99,999 using the [newton method][newton]
* `orders`: Compute the order ord(u) for each u in a cyclic group [<Zn,+>][cgroup] of integers modulo *n* under the group operation + (modulo *n*). Set the second argument *is_lcm* to true if you would like to compute the orders using the lowest common multiple and otherwise the program will use the greatest common divisor.
* `perfect`: Check if input argument is a perfect number.  Returns output as Unix style return code.
* `pythagorean_triple`: Prints all Pythagorean triples with the given c, if such triples exist. An intentionally very naive implementation.
* `quadratic`: The [quadratic formula][qf], including a hand-rolled implementation of square root.
* `recfact`: Compute *n!* using recursive function calls.
* `relative-primes`: Print all numbers relatively prime to *n* using [Euclidean algorithm][euclidean_into].
* `sieve`: Print all prime numbers up to *n* using the [Sieve of Eratosthenes][sievee].
* `sum-bit`: Print the number of 1-bits in the binary representation of the input integer.
* `sum-divisors`: Prints the positive integer divisors of the input integer, followed by the sum of the divisors.
* `sqrt`: Implements the [Newton–Raphson Method][newton] of approximating the square root of a number to arbitrary precision
* `sum-sq-diff`: Output the difference between the sum of the squares of the first *n* natural numbers and the square of their sum.
* `binary-fmt`: Print the binary format for the given positive integer.
* `adj2csr`: Convert a graph in [adjacency matrix][adj] format (dense representation) to [Compressed Sparse Row (CSR)][csr] format (sparse representation). The random graph is generated using the same [linear congruential generator][rng].
* `bubblesort`: Sorting algorithm that works by repeatedly swapping the adjacent elements if they are in wrong order. 
* `pow`: Computes the n^<sup>th</sup> power of a given (float) number.
* `up-arrow`: Computes [Knuth's up arrow][uparrow] notation, with the first argument being the number, the second argument being the number of Knuth's up arrows, and the third argument being the number of repeats.  
* `max-subarray`: solution to the classic Maximum Subarray problem.

Credit for several of these benchmarks goes to Alexa VanHattum and Gregory Yauney, who implemented them for their [global value numbering project][gvnblog].

[cgroup]: https://en.wikipedia.org/wiki/Cyclic_group#Cyclically_ordered_groups
[fizzbuzz]: https://wiki.c2.com/?FizzBuzzTest
[qf]: https://en.wikipedia.org/wiki/Quadratic_formula
[gvnblog]: https://www.cs.cornell.edu/courses/cs6120/2019fa/blog/global-value-numbering/
[sievee]: https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes
[collatz]: https://en.wikipedia.org/wiki/Collatz_conjecture
[ackermann]: https://en.wikipedia.org/wiki/Ackermann_function
[newton]: https://en.wikipedia.org/wiki/Newton%27s_method
[matmul]: https://en.wikipedia.org/wiki/Matrix_multiplication_algorithm#Iterative_algorithm
[rng]: https://en.wikipedia.org/wiki/Linear_congruential_generator
[euclidean_into]: https://en.wikipedia.org/wiki/Euclidean_algorithm
[euclid]: https://en.wikipedia.org/wiki/Euclidean_algorithm#Euclidean_division
[eight_queens]: https://en.wikipedia.org/wiki/Eight_queens_puzzle
[newton]: https://en.wikipedia.org/wiki/Newton%27s_method
[adj]: https://en.wikipedia.org/wiki/Adjacency_matrix
[csr]: https://en.wikipedia.org/wiki/Sparse_matrix
[armstrong]: https://en.wikipedia.org/wiki/Narcissistic_number
[trialdivision]:https://en.wikipedia.org/wiki/Trial_division
[adler32]: https://en.wikipedia.org/wiki/Adler-32
[uparrow]: https://en.wikipedia.org/wiki/Knuth%27s_up-arrow_notation
