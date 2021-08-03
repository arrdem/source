#!/bin/bash

TEST_HOST=sabod-rital.test.arrdem.com

function kook_setup {
  kook -g geo_test group delete
  kook -g rack_test_test group delete
  kook -H $TEST_HOST host delete
}

function kook_test {
  ##################################################
  # Group CRU
  if kook group create geo_test; then
    echo "[OK]   Geo group created"
  else
    echo "[FAIL] Geo group not created"
  fi

  if kook -g geo_test var create geo test; then
    echo "[OK]   Var created"
  else
    echo "[FAIL] Var create failed"
  fi

  if [ $(kook -g geo_test group details | jq '.geo_test.geo == "test"') == "true" ]; then
    echo "[OK]   Var read after write"
  else
    echo "[FAIL] Var not read back"
  fi

  # These two paths have already been tested
  kook group create rack_test_test
  kook -g rack_test_test var create rack test

  # Testing vars on parent groups
  if kook -g rack_test_test group add geo_test; then
    echo "[OK]   Group-group added"
  else
    echo "[FAIL] Group-group not added"
  fi

  if [ $(kook -g rack_test_test group details | jq '.rack_test_test.geo == "test"') == "true" ]; then
    echo "[OK]   'geo' var inherited from supergroup"
  else
    echo "[FAIL] Var not inherited!"
  fi

  if [ $(kook -g rack_test_test group details | jq '.rack_test_test.rack == "test"') == "true" ]; then
    echo "[OK]   'rack' var set"
  else
    echo "[FAIL] Var not set!"
  fi

  ##################################################
  # Host CRU
  if kook host create $TEST_HOST; then
    echo "[OK]   Host created"
  else
    echo "[FAIL] Host not created"
  fi

  if kook host list | grep -q $TEST_HOST > /dev/null; then
    echo "[OK]   Host read after write"
  else
    echo "[FAIL] Host not read"
  fi

  if kook -H $TEST_HOST var create foo bar; then
    echo "[OK]   Var created"
  else
    echo "[FAIL] Unable to create host var"
  fi

  if [ $(kook -H $TEST_HOST host details | jq ".[\"${TEST_HOST}\"].foo == \"bar\"") == "true" ]; then
    echo "[OK]   Able to read var back"
  else
    echo "[FAIL] Unable to read host var back!"
  fi

  # And for a host...
  if kook -H $TEST_HOST group add rack_test_test; then
    echo "[OK]   Added host to rack group"
  else
    echo "[FAIL] Unable to add host to rack group"
  fi

  # Checking that the host is in both group's list.
  if kook -g rack_test_test host list | grep -q $TEST_HOST; then
    echo "[OK]   Host is in the rack group"
  else
    echo "[FAIL] Host is not in the rack group!"
  fi

  # And in the geo's list.
  if kook -g geo_test host list | grep -q $TEST_HOST; then
    echo "[OK]   Host is in the geo group"
  else
    echo "[FAIL] Host is not in the geo group!"
  fi
}

function kook_teardown {
  kook_setup
}

kook_setup 1>/dev/null 2>/dev/null
kook_test
kook_teardown 1>/dev/null 2>/dev/null
