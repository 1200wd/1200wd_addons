# Account Bank Match module

## What does the Bank Match Module do?
This module matches every incoming payment with the correct invoice, order or account move. When a new payment comes in and a new bank statement line is created, the Account Bank Match module tries to find a suitable match. It looks for an invoice, sale order or account move with matches with the payment and add a score based on several rules.

When a match with a high enough score is found the payment can be automatically processed and reconciled. If you prefer you can also select the matching invoice or sale order manually from a list with more information.

Basically this module does two things:
 1. Extract partner, invoice, sale order information from bank statement lines and add them to a list of matches with a score
 2. Automatically process and reconcile bank payments
 
The module works out-of-the-box for most Odoo installations. The module includes a list of Match Rules which define which information to extract from the bank statement lines and a score system. You can however change these rules, add rules or set up your own score extraction and score system without through the web-interface, without any coding.


## Short Technical Description

### Bank Statement Line
When a new Bank Statement Line is created, or when the 'match' button is clicked in the Bank Statement view the match or account_bank_match method are called.

##### 1. Extract partner, invoice, sale order information from bank statement lines and add them to a list of matches with a score
* create(vals)
    * call match()
  
* action_statement_line_match()
    * call account_bank_match()
  
The match method looks for the most suitable match for a bank statement line. If 1 wining match is found and this is an invoice then add a link this invoice to the bank statement line. If the winning match is a sale order then create and invoice first.

* match(vals)
    * call account_bank_match()
    * call order_invoice_lookup(vals)
  
* account_bank_match()
    * remove old matches
    * winning_match = match_search()
    * add all matches and scores to match table
    * return wining match if found
    
* match_search()
    * Find partner through bank account number
    * Extract reference numbers from bank statement line
    * Run match rules on invoices, sale orders and account.moves
    * Calculate bonuses for already found matches
    * Sort, cleanup and return results
    
##### 2. Automatically process and reconcile bank payments

* auto_reconcile()
    * One invoice with an residual amount is found?
    * Then call pay_invoice_and_reconcile()
    * Link sale order, invoice and/or account moves with statement line
    
* pay_invoice_and_reconcile()
    * Create account move lines
    * Write off payment differences
    * Reconcile or Partial reconcile if not fully paid
    
    
## Account Bank Statement

Allows you to match all lines of a bank statement at once. 

* action_statement_match()
    * For every statement line:
        * Call match()
        * Call auto_reconcile()