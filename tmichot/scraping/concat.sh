#!/bin/sh
rm tmichot.csv
for x in *.csv ; do cat $x >> tmichot.csv ; done
