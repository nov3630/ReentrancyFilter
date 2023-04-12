// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.4.19;

contract Forwarder {
    address public parentAddress;
    function Forwarder()  {
        parentAddress = msg.sender;
    }

    function flush()  {
        if (!parentAddress.call.value(this.balance)()) {
            throw;
        }
    }
}
