COLLECTION_QUERY_STR = """
WITH TRANSACTIONS
     AS (  SELECT  DL.PARTY_ID,
                  DL.ORG_ID,
                  HCA.ACCOUNT_NUMBER,
                  DL.CUSTOMER_ID,
                  DL.GL_DATE,
                  DL.TRX_TYPE,
                  SUM (NVL (DL.DR_AMOUNT, 0)) DR_AMOUNT,
                  SUM (NVL (DL.CR_AMOUNT, 0)) CR_AMOUNT,
                  SUM (NVL (DL.DR_AMOUNT, 0)) - SUM (NVL (DL.CR_AMOUNT, 0))
                     AMOUNT
       FROM APPS.XX_AR_CUSTOMER_DTL_LEDGER DL,  HZ_CUST_ACCOUNTS HCA
            WHERE 1 = 1
            AND  DL.PARTY_ID = HCA.PARTY_ID
             AND  DL.CUSTOMER_ID = HCA.CUST_ACCOUNT_ID
            -- AND HCA.ACCOUNT_NUMBER = :witp_code
            AND  DL.GL_DATE <= TRUNC (SYSDATE - 1)
            AND DL.ORG_ID IN (222, 522)
         GROUP BY DL.PARTY_ID,
                  DL.ORG_ID,
                  HCA.ACCOUNT_NUMBER,
                  DL.CUSTOMER_ID,
                 DL.GL_DATE,
                 DL.TRX_TYPE),
     CUSTOMER
     AS (SELECT DISTINCT HP.PARTY_ID,
                         HCA.ACCOUNT_NUMBER,
                         SITE_USE.ORG_ID,
                         HCA.CUST_ACCOUNT_ID,
                         HCA.ACCOUNT_NAME,
                         HP.PARTY_NAME,
                         HP.ADDRESS1,
                         HCA.SALES_CHANNEL_CODE Customer_Category,
                         HCA.CUSTOMER_CLASS_CODE Exclusive_Status,
                         HCA.STATUS
           FROM HZ_PARTIES HP,
                HZ_CUST_ACCOUNTS HCA,
                APPS.HZ_CUST_ACCT_SITES_ALL ACCT_USE,
                APPS.HZ_CUST_SITE_USES_ALL SITE_USE
          WHERE     HP.PARTY_ID = HCA.PARTY_ID
                AND HCA.CUST_ACCOUNT_ID = ACCT_USE.CUST_ACCOUNT_ID
                AND ACCT_USE.CUST_ACCT_SITE_ID = SITE_USE.CUST_ACCT_SITE_ID
                AND HCA.ACCOUNT_NUMBER = :witp_code
                AND PARTY_TYPE = 'ORGANIZATION'
                AND HCA.SALES_CHANNEL_CODE = 'CORPORATE WITP'),
SALES   AS (
SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
         NVL (SUM (T.SALES_AMOUNT), 0) SALES_AMOUNT
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 0 SALES_AMOUNT
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   NVL (SUM (DR_AMOUNT), 0) SALES_AMOUNT
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                   AND UPPER (TRX_TYPE) IN ('GO-LIVE OPENING BALANCE', 'SALES')
                   AND GL_DATE BETWEEN ADD_MONTHS (TRUNC (SYSDATE - 1), -6)
                                   AND TRUNC (SYSDATE - 1)
          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER),

  TOTAL_SALES   AS (  SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
         NVL (SUM (T.SALES_AMOUNT), 0) TOTAL_SALES_AMOUNT
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 0 SALES_AMOUNT
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   NVL (SUM (DR_AMOUNT), 0) SALES_AMOUNT
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                   AND UPPER (TRX_TYPE) IN ('GO-LIVE OPENING BALANCE', 'SALES')
          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER),
    RECEIPT AS (
SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
         NVL (SUM (T.CR_AMOUNT), 0) CR_AMOUNT
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 0 CR_AMOUNT
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   NVL (SUM (CR_AMOUNT), 0) CR_AMOUNT
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                    AND UPPER (TRX_TYPE) = 'RECEIPTS'
                   AND GL_DATE BETWEEN ADD_MONTHS (TRUNC (SYSDATE - 1), -6)
                                   AND TRUNC (SYSDATE - 1)
          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER),
 TOTAL_RECEIPT
     AS (
SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
         NVL (SUM (T.CR_AMOUNT), 0) TOTAL_RECIPT_AMOUNT
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 0 CR_AMOUNT
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   NVL (SUM (CR_AMOUNT), 0) CR_AMOUNT
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                    AND UPPER (TRX_TYPE) = 'RECEIPTS'
                   AND GL_DATE BETWEEN ADD_MONTHS (TRUNC (SYSDATE - 1), -6)
                                   AND TRUNC (SYSDATE - 1)
          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER),
OPENING_BALANCE AS (

SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
         NVL (SUM (T.OPENING_AMOUNT), 0) OPENING_AMOUNT
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 0 OPENING_AMOUNT
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   NVL (SUM (AMOUNT), 0) OPENING_AMOUNT
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                   AND GL_DATE < ADD_MONTHS (TRUNC (SYSDATE - 1), -6)
          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER),

CLOSING_BALANCE AS (
SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
         NVL (SUM (T.CLOSING_BALANCE), 0) CLOSING_BALANCE
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 0 CLOSING_BALANCE
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   NVL (SUM (AMOUNT), 0) CLOSING_BALANCE
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                   AND GL_DATE < TRUNC (SYSDATE - 1)
          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER),
 AVERAGE_BALANCE
     AS (SELECT O.PARTY_ID,
                O.ORG_ID,
                O.ACCOUNT_NUMBER,
                ROUND ( (O.OPENING_AMOUNT + C.CLOSING_BALANCE) / 2, 2)
                   AVERAGE_BALANCE
           FROM OPENING_BALANCE O
                LEFT JOIN CLOSING_BALANCE C
                   ON O.PARTY_ID = C.PARTY_ID AND O.ORG_ID = C.ORG_ID),
     MONTHLY_COLL_RATIO
     AS (SELECT ORG_ID,
                ACCOUNT_NUMBER,
                PARTY_ID,
                ROUND ( ( (CR_AMOUNT * 30) / 180), 2) MONTHLY_COLL_RATIO
           FROM RECEIPT),
     AVERAGE_COLL_RATIO
     AS (SELECT DISTINCT
                M.ORG_ID,
                M.PARTY_ID,
                M.ACCOUNT_NUMBER,
                ROUND (
                     COALESCE (
                        M.MONTHLY_COLL_RATIO / NULLIF (A.AVERAGE_BALANCE, 0),
                        0)
                   * 100,
                   2)
                   AS AVERAGE_COLL_RATIO
           FROM MONTHLY_COLL_RATIO M, AVERAGE_BALANCE A
          WHERE M.PARTY_ID = A.PARTY_ID AND M.ORG_ID = A.ORG_ID),
     LAST_SIX_MON_SALES_AVG
     AS (SELECT PARTY_ID,
                ORG_ID,
                ACCOUNT_NUMBER,
                ROUND (SALES_AMOUNT / 6, 2) AVG_SALE_AMOUNT
           FROM SALES
          WHERE ACCOUNT_NUMBER = :witp_code),
     LAST_SIX_MON_COLL_AVG
     AS (SELECT PARTY_ID,
                ORG_ID,
                ACCOUNT_NUMBER,
                ROUND (CR_AMOUNT / 6, 2) AVG_RECEIPT_AMOUNT
           FROM RECEIPT
          WHERE ACCOUNT_NUMBER = :witp_code),
    LAST_SALE_DATE  AS (
SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
          MAX (T.LAST_SALE_DATE) AS LAST_SALE_DATE
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 NULL LAST_SALE_DATE
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   MAX (GL_DATE) AS LAST_SALE_DATE
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                   AND UPPER (TRX_TYPE) IN ('GO-LIVE OPENING BALANCE', 'SALES')

          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER),
 LAST_RECEIPT_DATE  AS (
     SELECT T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER,
          MAX (T.LAST_RECEIPT_DATE) AS LAST_RECEIPT_DATE
    FROM (SELECT PARTY_ID,
                 ORG_ID,
                 CUST_ACCOUNT_ID CUSTOMER_ID,
                 NULL LAST_RECEIPT_DATE
            FROM CUSTOMER
           WHERE ACCOUNT_NUMBER = :witp_code
          UNION ALL
            SELECT PARTY_ID,
                   ORG_ID,
                   CUSTOMER_ID,
                   MAX (GL_DATE) AS LAST_RECEIPT_DATE
              FROM TRANSACTIONS
             WHERE     1 = 1
                   AND ACCOUNT_NUMBER = :witp_code
                  AND UPPER (TRX_TYPE) = 'RECEIPTS'

          GROUP BY PARTY_ID, ORG_ID, CUSTOMER_ID) T,
         CUSTOMER R
   WHERE     T.PARTY_ID = R.PARTY_ID
         AND T.ORG_ID = R.ORG_ID
         AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY T.PARTY_ID,
         T.ORG_ID,
         T.CUSTOMER_ID,
         R.ACCOUNT_NUMBER)
SELECT DISTINCT
       ACR.ORG_ID,
       ACR.PARTY_ID,
       ACR.ACCOUNT_NUMBER,
       (CASE
           WHEN ACR.ORG_ID = 222 THEN 'WDC'
           WHEN ACR.ORG_ID = 522 THEN 'WCL'
           ELSE NULL
        END)
          AS ORG_TYPE,
       ACR.AVERAGE_COLL_RATIO,
       LTM.AVG_RECEIPT_AMOUNT,
       LSA.AVG_SALE_AMOUNT,
       SD.LAST_SALE_DATE,
       RD.LAST_RECEIPT_DATE,
       OP.OPENING_AMOUNT,
       CB.CLOSING_BALANCE,
       TS.TOTAL_SALES_AMOUNT,
       TR.TOTAL_RECIPT_AMOUNT
  FROM AVERAGE_COLL_RATIO ACR,
       LAST_SIX_MON_COLL_AVG LTM,
       LAST_SIX_MON_SALES_AVG LSA,
       LAST_SALE_DATE SD,
       LAST_RECEIPT_DATE RD,
       CLOSING_BALANCE CB,
       TOTAL_SALES TS,
       TOTAL_RECEIPT TR,
       OPENING_BALANCE OP

 WHERE     1 = 1
       AND ACR.PARTY_ID = LTM.PARTY_ID
       AND ACR.ORG_ID = LTM.ORG_ID
       AND ACR.PARTY_ID = LSA.PARTY_ID
       AND ACR.ORG_ID = LSA.ORG_ID
       AND ACR.PARTY_ID = SD.PARTY_ID
       AND ACR.ORG_ID = SD.ORG_ID
       AND ACR.PARTY_ID = RD.PARTY_ID
       AND ACR.ORG_ID = RD.ORG_ID
       AND ACR.PARTY_ID = CB.PARTY_ID
       AND ACR.ORG_ID = CB.ORG_ID
       AND ACR.PARTY_ID = TS.PARTY_ID
       AND ACR.ORG_ID = TS.ORG_ID
       AND ACR.PARTY_ID = TR.PARTY_ID
       AND ACR.ORG_ID = TR.ORG_ID
       AND ACR.PARTY_ID = OP.PARTY_ID
       AND ACR.ORG_ID = OP.ORG_ID
       ORDER BY  ACR.ORG_ID ASC
"""
