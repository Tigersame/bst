#!/usr/bin/env python3
# Copyright (c) 2018 Daniel Kraft
# Distributed under the MIT/X11 software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# Tests the interaction between names and the UTXO set.

from test_framework.names import NameTestFramework
from test_framework.util import *


class NameUtxoTest (NameTestFramework):

  def set_test_params (self):
    self.setup_name_test ([[]] * 1)

  def run_test (self):
    node = self.nodes[0]

    # Prepare the scene:  We want one stale name_new, one expired name
    # and one unexpired name.

    addr = node.getnewaddress ()
    newStale = node.name_new ("d/never-registered", {"destAddress": addr})
    txidStale = newStale[0]
    txStale = node.getrawtransaction (txidStale)
    voutStale = self.rawtxOutputIndex (0, txStale, addr)

    newExpired = node.name_new ("d/expired")
    newActive = node.name_new ("d/active")
    node.generate (10)
    self.firstupdateName (0, "d/expired", newExpired, "{}")
    node.generate (20)
    self.firstupdateName (0, "d/active", newActive, "{}")
    node.generate (20)

    # The never used name_new should be in the UTXO set.
    txo = node.gettxout (txidStale, voutStale)
    assert_equal (txo['scriptPubKey']['nameOp']['op'], 'name_new')

    # The expired name should *not* be in the UTXO set.
    data = node.name_show ("d/expired")
    assert_equal (data['expired'], True)
    assert_equal (node.gettxout (data['txid'], data['vout']), None)

    # The active name should be there.
    data = node.name_show ("d/active")
    assert_equal (data['expired'], False)
    txo = node.gettxout (data['txid'], data['vout'])
    nameOp = txo['scriptPubKey']['nameOp']
    assert_equal (nameOp['op'], 'name_firstupdate')
    assert_equal (nameOp['name'], 'd/active')

    # Verify the expected result for gettxoutsetinfo.  The unused name_new
    # should be in there, as well as the active name.  The expired name
    # should be removed from it (as tested already above).
    data = node.gettxoutsetinfo ()
    height = data['height']
    assert_equal (height, 2050)
    assert_equal (data['txouts'], 2052)
    amount = data['amount']
    assert_equal (amount['names'], Decimal ('0.0002'))
    assert_equal (amount['total'], amount['names'] + amount['coins'])
    mined = 1499 * 50 + (height - 1499) * 25
    assert_equal (amount['total'], mined - Decimal ('0.0001'))


if __name__ == '__main__':
  NameUtxoTest ().main ()
