max_invoice_day_count_sql = """
SELECT
	MAX (DAY_COUNT) AS DAY_COUNT
FROM
	(
	SELECT
		OU.NAME COMPANY,
		CUST_SITE.CUSTOMER_NUMBER,
		CUST_SITE.CUSTOMER_ID,
		CUST_SITE.CUSTOMER_NAME,
		CT.TRX_NUMBER,
		DIST.GL_DATE,
		NVL((SELECT NAME FROM APPS.RA_TERMS WHERE TERM_ID = CT.TERM_ID), 'Credit Memo') TERM,
		SYSDATE SYS_DATE,
		( TO_DATE (TO_DATE ( SYSDATE,
		'DD-MON-RRRR'))
                            - DIST.GL_DATE)
                              DAY_COUNT,
		(DIST.ACCTD_AMOUNT - ABS (NVL (CM_AMOUNT,
		0)))
                           - NVL (RCT_AMOUNT,
		0)
                           + NVL (RFN_AMOUNT,
		0)
                           + NVL (CMINV_AMOUNT,
		0)
                              BALANCE_DUE
	FROM
		APPS.RA_CUSTOMER_TRX_ALL CT,
		APPS.hr_operating_units ou,
		APPS.RA_CUST_TRX_LINE_GL_DIST_ALL DIST,
		apps.SOFTLN_AR_CUSTOMERS_ALL_V CUST_SITE,
		APPS.RA_CUST_TRX_TYPES_ALL RCTT,
		GL_CODE_COMBINATIONS GCC,
		APPS.FND_FLEX_VALUES_VL vl,
		APPS.RA_BATCH_SOURCES_ALL SR,
		(
		SELECT
			APPLIED_CUSTOMER_TRX_ID,
			SUM (ACCTD_AMOUNT_APPLIED_TO) CM_AMOUNT
		FROM
			APPS.AR_RECEIVABLE_APPLICATIONS_ALL
		WHERE
			DISPLAY = 'Y'
			AND APPLICATION_TYPE = 'CM'
			AND TRUNC (GL_DATE) <=
                                              TO_DATE ( SYSDATE,
			'DD-MON-RRRR')
		GROUP BY
			APPLIED_CUSTOMER_TRX_ID) CM,
		(
		SELECT
			APPLIED_CUSTOMER_TRX_ID,
			SUM (ACCTD_AMOUNT_APPLIED_TO) RCT_AMOUNT
		FROM
			APPS.AR_RECEIVABLE_APPLICATIONS_ALL
		WHERE
			DISPLAY = 'Y'
			AND APPLICATION_TYPE <> 'CM'
			AND TRUNC (GL_DATE) <=
                                              TO_DATE ( SYSDATE,
			'DD-MON-RRRR')
		GROUP BY
			APPLIED_CUSTOMER_TRX_ID) Receipt,
		(
		SELECT
			CUSTOMER_TRX_ID,
			SUM (ACCTD_AMOUNT_APPLIED_TO) RFN_AMOUNT
		FROM
			APPS.AR_RECEIVABLE_APPLICATIONS_ALL
		WHERE
			DISPLAY = 'Y'
			AND APPLICATION_TYPE = 'CM'
			AND APPLICATION_REF_TYPE = 'AP_REFUND_REQUEST'
			AND TRUNC (GL_DATE) <=
                                              TO_DATE ( SYSDATE,
			'DD-MON-RRRR')
		GROUP BY
			CUSTOMER_TRX_ID) REFUND,
		(
		SELECT
			CUSTOMER_TRX_ID,
			SUM (ACCTD_AMOUNT_APPLIED_TO) CMINV_AMOUNT
		FROM
			APPS.AR_RECEIVABLE_APPLICATIONS_ALL
		WHERE
			DISPLAY = 'Y'
			AND APPLICATION_TYPE = 'CM'
			AND NVL (APPLICATION_REF_TYPE,
			'XX') = 'XX'
				AND TRUNC (GL_DATE) <=
                                              TO_DATE ( SYSDATE,
				'DD-MON-RRRR')
			GROUP BY
				CUSTOMER_TRX_ID) CM_INV
	WHERE
		DIST.ACCOUNT_CLASS = 'REC'
		AND CT.CUSTOMER_TRX_ID = DIST.CUSTOMER_TRX_ID
		AND CT.CUST_TRX_TYPE_ID = RCTT.CUST_TRX_TYPE_ID
		AND ct.org_id = rctt.org_id
		AND ct.org_id = ou.organization_id
		AND CUST_SITE.CUSTOMER_ID = CT.BILL_TO_CUSTOMER_ID
		AND CT.COMPLETE_FLAG = 'Y'
		AND VL.FLEX_VALUE_SET_ID = 1016488
		AND GCC.SEGMENT5 = VL.FLEX_VALUE
		AND DIST.CODE_COMBINATION_ID = GCC.CODE_COMBINATION_ID
		AND CT.CUSTOMER_TRX_ID = CM.APPLIED_CUSTOMER_TRX_ID(+)
		AND CT.CUSTOMER_TRX_ID =
                                  RECEIPT.APPLIED_CUSTOMER_TRX_ID(+)
		AND CT.CUSTOMER_TRX_ID = REFUND.CUSTOMER_TRX_ID(+)
		AND CT.CUSTOMER_TRX_ID = CM_INV.CUSTOMER_TRX_ID(+)
		AND CT.BATCH_SOURCE_ID = SR.BATCH_SOURCE_ID
		AND CT.ORG_ID = SR.ORG_ID
		AND (DIST.ACCTD_AMOUNT - ABS (NVL (CM_AMOUNT,
		0)))
                               - NVL (RCT_AMOUNT,
		0)
                               + NVL (RFN_AMOUNT,
		0)
                               + NVL (CMINV_AMOUNT,
		0) <> 0
		AND CT.ORG_ID IN (222, 522)
		AND CUST_SITE.CUSTOMER_NUMBER = :witp_code
		AND TRUNC (DIST.GL_DATE) <=
                                  TO_DATE ( SYSDATE,
		'DD-MON-RRRR')
	ORDER BY
		1,
		5)
"""

party_grading_sql = """
WITH TRANSACTIONS AS (
SELECT
	DISTINCT DL.PARTY_ID,
	DL.ORG_ID,
	DL.GL_DATE,
	DL.TRX_TYPE,
	SUM(NVL(DL.DR_AMOUNT, 0)) DR_AMOUNT,
	SUM( NVL (DL.CR_AMOUNT, 0)) CR_AMOUNT,
	SUM(NVL(DL.DR_AMOUNT, 0)) - SUM( NVL (DL.CR_AMOUNT, 0)) AMOUNT
FROM
	APPS.XX_AR_CUSTOMER_DTL_LEDGER DL
WHERE
	DL.GL_DATE <= TRUNC (SYSDATE - 1)
	AND DL.ORG_ID IN (222, 522)
GROUP BY
	DL.PARTY_ID,
	DL.ORG_ID,
	DL.GL_DATE,
	DL.TRX_TYPE
       ),

CUSTOMER AS (
SELECT
	DISTINCT
                  HP.PARTY_ID,
	HCA.ACCOUNT_NUMBER,
	HCA.ACCOUNT_NAME,
	HP.PARTY_NAME,
	HP.ADDRESS1,
	HCA.SALES_CHANNEL_CODE SALES_CHANNEL_CODE,
	HCA.CUSTOMER_CLASS_CODE Exclusive_Status,
	HCA.STATUS
FROM
	HZ_PARTIES HP,
	HZ_CUST_ACCOUNTS HCA
WHERE
	HP.PARTY_ID = HCA.PARTY_ID
	AND HCA.ACCOUNT_NUMBER = :witp_code
	AND PARTY_TYPE = 'ORGANIZATION'
	AND HCA.SALES_CHANNEL_CODE = 'CORPORATE WITP'),
OPENING_BALANCE AS(
SELECT
	T.PARTY_ID,
	R.ACCOUNT_NUMBER,
	NVL(SUM(T.OPENING_AMOUNT), 0) OPENING_AMOUNT
FROM
	(
	SELECT
		PARTY_ID,
		NULL OPENING_AMOUNT
	FROM
		TRANSACTIONS
UNION ALL
	SELECT
		PARTY_ID,
		NVL(SUM(AMOUNT), 0) OPENING_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		1 = 1
		-- AND GL_DATE <= '20-NOV-2023'
		AND GL_DATE < ADD_MONTHS (TRUNC (SYSDATE - 1),
		-6)
	GROUP BY
		PARTY_ID) T
         ,
	CUSTOMER R
WHERE
	T.PARTY_ID = R.PARTY_ID
	AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY
	T.PARTY_ID,
	R.ACCOUNT_NUMBER

         ),
CLOSING_BALANCE AS(
SELECT
	T.PARTY_ID ,
	R.ACCOUNT_NUMBER ,
	NVL(SUM(T.CLOSING_BALANCE), 0) CLOSING_BALANCE
FROM
	(
	SELECT
		PARTY_ID,
		NULL CLOSING_BALANCE
	FROM
		TRANSACTIONS
UNION ALL
	SELECT
		PARTY_ID,
		NVL(SUM(AMOUNT), 0) CLOSING_BALANCE
	FROM
		TRANSACTIONS
	WHERE
		1 = 1
		-- AND GL_DATE < '21-MAY-2024'
		AND GL_DATE < TRUNC (SYSDATE - 1)
	GROUP BY
		PARTY_ID) T
         ,
	CUSTOMER R
WHERE
	T.PARTY_ID = R.PARTY_ID
	AND R.ACCOUNT_NUMBER = :witp_code
GROUP BY
	T.PARTY_ID ,
	R.ACCOUNT_NUMBER

          ),
RECEIPTS AS(
SELECT
	T.PARTY_ID,
	R.ACCOUNT_NUMBER,
	T.CR_AMOUNT
FROM
	(
	SELECT
		PARTY_ID,
		NVL(SUM(CR_AMOUNT), 0) CR_AMOUNT
	FROM
		(
		SELECT
			PARTY_ID,
			NULL CR_AMOUNT
		FROM
			TRANSACTIONS
	UNION ALL
		SELECT
			PARTY_ID,
			NVL (SUM (CR_AMOUNT),
			0) CR_AMOUNT
		FROM
			TRANSACTIONS
		WHERE
			1 = 1
			AND UPPER (TRX_TYPE) = 'RECEIPTS'
				AND GL_DATE BETWEEN ADD_MONTHS (TRUNC (SYSDATE - 1),
				-6) AND TRUNC (SYSDATE - 1)
			GROUP BY
				PARTY_ID)
	GROUP BY
		PARTY_ID ) T
         ,
	CUSTOMER R
WHERE
	T.PARTY_ID = R.PARTY_ID
	AND R.ACCOUNT_NUMBER = :witp_code
 )



SELECT
	ACCOUNT_NUMBER WITP_CODE,
	PARTY_NAME,
	IS_ALL_DOC_UP,
	RATING_CERTIFICATE,
	PARTY_STATUS,
	CUS_CATEGORY,
	CLOSING_BALANCE,
	AVERAGE_COLLECTION_RATIO,
	CATEGORY GRADE
FROM
	(
	SELECT
		DISTINCT ACCOUNT_NUMBER,
		PARTY_ID,
		PARTY_NAME,
		SALES_CHANNEL_CODE,
		IS_ALL_DOC_UP,
		RATING_CERTIFICATE,
		PARTY_STATUS,
		CUS_CATEGORY,
		CASE
			WHEN KAM_NAME IS NOT NULL THEN KAM_NAME || ' (' || TSO_NAME || ')'
			ELSE NULL
		END AS KAM_NAME,
		CASE
			WHEN SC_EMP_NAME IS NOT NULL THEN SC_EMP_NAME || ' (' || SR_NAME || ')'
			ELSE NULL
		END AS COORDINATOR_NAME,
		CASE
			WHEN IS_ALL_DOC_UP IN ('YES', 'OTHERS')
				AND CLOSING_BALANCE <= 0
				AND ( AVERAGE_COLLECTION_RATIO >= 100
					OR AVERAGE_COLLECTION_RATIO <0)
				AND ( RATING_CERTIFICATE = 'AAA'
					OR RATING_CERTIFICATE = 'AA'
					OR RATING_CERTIFICATE = 'A')
          THEN
             'A'
				WHEN IS_ALL_DOC_UP IN ('YES', 'OTHERS')
					AND ( AVERAGE_COLLECTION_RATIO >= 80
						OR AVERAGE_COLLECTION_RATIO <0)
					AND ( RATING_CERTIFICATE = 'AAA'
						OR RATING_CERTIFICATE = 'AA'
						OR RATING_CERTIFICATE = 'A'
						OR RATING_CERTIFICATE = 'BBB')
          THEN
             'B'
					WHEN IS_ALL_DOC_UP IN ('YES', 'OTHERS')
						AND ( AVERAGE_COLLECTION_RATIO >= 60
							OR AVERAGE_COLLECTION_RATIO <0)
						AND ( RATING_CERTIFICATE = 'AAA'
							OR RATING_CERTIFICATE = 'AA'
							OR RATING_CERTIFICATE = 'A'
							OR RATING_CERTIFICATE = 'BBB'
							OR RATING_CERTIFICATE = 'BB')
          THEN
             'C'
						WHEN IS_ALL_DOC_UP IN ('YES', 'OTHERS')
							AND ( AVERAGE_COLLECTION_RATIO >= 40
								OR AVERAGE_COLLECTION_RATIO <0)
							--  AND RATING_CERTIFICATE NOT IN ('AAA','AA','A','BBB','BBB')
          THEN
             'D'
							ELSE 'NON CATEGORIZED'
						END
          AS CATEGORY,
						OPENING_BALANCE,
						CLOSING_BALANCE,
						AVERAGE_BALANCE,
						RECEIPT_AMOUNT,
						MONTHLY_COLLECTION_RATIO,
						AVERAGE_COLLECTION_RATIO
					FROM
						(
						SELECT
							DISTINCT C.PARTY_ID,
							c.PARTY_NAME,
							C.ACCOUNT_NUMBER,
							C.ACCOUNT_NAME,
							c.SALES_CHANNEL_CODE,
							XX.IS_ALL_DOC_UP,
							XX.RATING_CERTIFICATE,
							XX.PARTY_STATUS,
							XX.CUS_CATEGORY,
							XX.TSO_NAME,
							(
							SELECT
								Q1.EMP_NAME
							FROM
								APPS.XX_HRMS_MASTER_DATA Q1
							WHERE
								Q1.EMP_CODE = XX.TSO_NAME) KAM_NAME,
							XX.SR_NAME,
							(
							SELECT
								Q1.EMP_NAME
							FROM
								APPS.XX_HRMS_MASTER_DATA Q1
							WHERE
								Q1.EMP_CODE = XX.SR_NAME) SC_EMP_NAME,
							NVL (OB.OPENING_AMOUNT,
							0) OPENING_BALANCE,
							NVL (CO.CLOSING_BALANCE,
							0) CLOSING_BALANCE,
							(NVL (OB.OPENING_AMOUNT,
							0) + NVL (CO.CLOSING_BALANCE,
							0)) / 2
                  AVERAGE_BALANCE,
							(RCT.CR_AMOUNT) RECEIPT_AMOUNT,
							ROUND ( ( (RCT.CR_AMOUNT * 30) / 180),
							2)
                  MONTHLY_COLLECTION_RATIO,
							CASE
								WHEN COALESCE (CO.CLOSING_BALANCE,
								0) = 0
                  THEN
                     0
								ELSE
                     ROUND (
                          ROUND (
                             (COALESCE (RCT.CR_AMOUNT,
								0) * 30) / 180,
								2)
                        / ( ( COALESCE (OB.OPENING_AMOUNT,
								0)
                              + COALESCE (CO.CLOSING_BALANCE,
								0))
                           / 2),
								2)* 100
							END
                  AS AVERAGE_COLLECTION_RATIO
						FROM
							CUSTOMER C
						LEFT JOIN TRANSACTIONS T ON
							C.PARTY_ID = T.PARTY_ID
						LEFT JOIN APPS.XX_CUSTOMER_INFO XX ON
							C.PARTY_ID = XX.PARTY_ID
						LEFT JOIN OPENING_BALANCE OB ON
							C.PARTY_ID = OB.PARTY_ID
						LEFT JOIN CLOSING_BALANCE CO ON
							C.PARTY_ID = CO.PARTY_ID
						LEFT JOIN RECEIPTS RCT ON
							C.PARTY_ID = RCT.PARTY_ID
)
)
"""

party_status_sql = """
SELECT
	WITP_CODE,
	CUSTOMER_STATUS
FROM
	(WITH CUSTOMER_ZONE
             AS (
	SELECT
		CUSTOMER_ID,
		CUSTOMER_NUMBER WITP_CODE,
		SALES_CHANNEL_CODE,
		AREA,
		CUSTOMER_NAME,
		SUM (BALANCE_DUE) BALANCE_DUE,
		(CASE
			WHEN SUM (PLUS_DAYS_360) > 0
                              THEN
                                 'BAD'
			WHEN SUM (DAYS_360) > 0
			AND SUM (PLUS_DAYS_360) <= 0
                              THEN
                                 'DOUBTFUL'
			WHEN SUM (DAYS_270) > 0
			AND (SUM (PLUS_DAYS_360) + SUM (DAYS_360)) <=
                                          0
                              THEN
                                 'WATCHFUL'
			WHEN SUM (DAYS_180) > 0
			AND ( SUM (PLUS_DAYS_360)
                                        + SUM (DAYS_360)
                                        + SUM (DAYS_270)) <= 0
                              THEN
                                 'SUBSTANDARD'
			WHEN SUM (DAYS_90) > 0
			AND ( SUM (PLUS_DAYS_360)
                                        + SUM (DAYS_360)
                                        + SUM (DAYS_270)
                                        + SUM (DAYS_360)) <= 0
                              THEN
                                 'STANDARD'
			ELSE
                                 'STANDARD'
		END)
                             CUSTOMER_STATUS
	FROM
		(
		SELECT
			--COMPANY,
			SALES_CHANNEL_CODE,
			AREA,
			CUSTOMER_ID,
			CUSTOMER_NUMBER,
			CUSTOMER_NAME,
			(CASE
				WHEN DAY_COUNT < 90
                                        THEN
                                           SUM (BALANCE_DUE)
				ELSE
                                           0
			END)
                                       DAYS_90,
			(CASE
				WHEN DAY_COUNT > 90
				AND DAY_COUNT < 181
                                        THEN
                                           SUM (BALANCE_DUE)
				ELSE
                                           0
			END)
                                       DAYS_180,
			(CASE
				WHEN DAY_COUNT > 180
				AND DAY_COUNT < 271
                                        THEN
                                           SUM (BALANCE_DUE)
				ELSE
                                           0
			END)
                                       DAYS_270,
			(CASE
				WHEN DAY_COUNT > 270
				AND DAY_COUNT <= 365
                                        THEN
                                           SUM (BALANCE_DUE)
				ELSE
                                           0
			END)
                                       DAYS_360,
			(CASE
				WHEN DAY_COUNT > 365
                                        THEN
                                           SUM (BALANCE_DUE)
				ELSE
                                           0
			END)
                                       PLUS_DAYS_360,
			SUM (BALANCE_DUE) BALANCE_DUE
		FROM
			(
			SELECT
				SR.NAME,
				GCC.SEGMENT5 || '-' || VL.DESCRIPTION
                                               GL_CCID,
				UPPER (RCTT.TYPE),
				CUST_SITE.CUSTOMER_CATEGORY_CODE
                                               SALES_CHANNEL_CODE,
				CUST_SITE.AREA,
				CUST_SITE.CUSTOMER_ID,
				CUST_SITE.CUSTOMER_NUMBER,
				CUST_SITE.CUSTOMER_NAME,
				CT.TRX_NUMBER,
				DIST.GL_DATE,
				SYSDATE SYS_DATE,
				( TO_DATE (
                                                  TO_DATE (:P_END_DATE,
				'DD-MON-RRRR'))
				--:P_END_DATE
                                             - DIST.GL_DATE)
                                               DAY_COUNT,
				( DIST.ACCTD_AMOUNT
                                               - ABS (NVL (CM_AMOUNT,
				0)))
                                            - NVL (RCT_AMOUNT,
				0)
                                            + NVL (RFN_AMOUNT,
				0)
                                            + NVL (CMINV_AMOUNT,
				0)
                                               BALANCE_DUE
			FROM
				APPS.RA_CUSTOMER_TRX_ALL CT,
				APPS.hr_operating_units ou,
				APPS.RA_CUST_TRX_LINE_GL_DIST_ALL DIST,
				apps.SOFTLN_AR_CUSTOMERS_ALL_V CUST_SITE,
				APPS.RA_CUST_TRX_TYPES_ALL RCTT,
				GL_CODE_COMBINATIONS GCC,
				APPS.FND_FLEX_VALUES_VL vl,
				APPS.RA_BATCH_SOURCES_ALL SR,
				(
				SELECT
					APPLIED_CUSTOMER_TRX_ID,
					SUM (ACCTD_AMOUNT_APPLIED_TO)
                                                         CM_AMOUNT
				FROM
					APPS.AR_RECEIVABLE_APPLICATIONS_ALL
				WHERE
					DISPLAY = 'Y'
					AND APPLICATION_TYPE = 'CM'
					AND TRUNC (GL_DATE) <=
                                                             TO_DATE (
                                                                :P_END_DATE,
					'DD-MON-RRRR')
					---:P_END_DATE
				GROUP BY
					APPLIED_CUSTOMER_TRX_ID) CM,
				(
				SELECT
					APPLIED_CUSTOMER_TRX_ID,
					SUM (ACCTD_AMOUNT_APPLIED_TO)
                                                         RCT_AMOUNT
				FROM
					APPS.AR_RECEIVABLE_APPLICATIONS_ALL
				WHERE
					DISPLAY = 'Y'
					AND APPLICATION_TYPE <> 'CM'
					AND TRUNC (GL_DATE) <=
                                                             TO_DATE (
                                                                :P_END_DATE,
					'DD-MON-RRRR')
				GROUP BY
					APPLIED_CUSTOMER_TRX_ID)
                                            Receipt,
				(
				SELECT
					CUSTOMER_TRX_ID,
					SUM (ACCTD_AMOUNT_APPLIED_TO)
                                                         RFN_AMOUNT
				FROM
					APPS.AR_RECEIVABLE_APPLICATIONS_ALL
				WHERE
					DISPLAY = 'Y'
					AND APPLICATION_TYPE = 'CM'
					AND APPLICATION_REF_TYPE =
                                                             'AP_REFUND_REQUEST'
					AND TRUNC (GL_DATE) <=
                                                             TO_DATE (
                                                                :P_END_DATE,
					'DD-MON-RRRR')
				GROUP BY
					CUSTOMER_TRX_ID) REFUND,
				(
				SELECT
					CUSTOMER_TRX_ID,
					SUM (ACCTD_AMOUNT_APPLIED_TO)
                                                         CMINV_AMOUNT
				FROM
					APPS.AR_RECEIVABLE_APPLICATIONS_ALL
				WHERE
					DISPLAY = 'Y'
					AND APPLICATION_TYPE = 'CM'
					AND NVL (
                                                             APPLICATION_REF_TYPE,
					'XX') = 'XX'
						AND TRUNC (GL_DATE) <=
                                                             TO_DATE (
                                                                :P_END_DATE,
						'DD-MON-RRRR')
					GROUP BY
						CUSTOMER_TRX_ID) CM_INV
			WHERE
				DIST.ACCOUNT_CLASS = 'REC'
				AND CT.CUSTOMER_TRX_ID =
                                                   DIST.CUSTOMER_TRX_ID
				AND CT.CUST_TRX_TYPE_ID =
                                                   RCTT.CUST_TRX_TYPE_ID
				AND ct.org_id = rctt.org_id
				AND ct.org_id = ou.organization_id
				AND CUST_SITE.CUSTOMER_ID = CT.BILL_TO_CUSTOMER_ID
				AND CT.COMPLETE_FLAG = 'Y'
				AND VL.FLEX_VALUE_SET_ID = 1016488
				AND GCC.SEGMENT5 = VL.FLEX_VALUE
				AND DIST.CODE_COMBINATION_ID = GCC.CODE_COMBINATION_ID
				AND CT.CUSTOMER_TRX_ID =
                                                   CM.APPLIED_CUSTOMER_TRX_ID(+)
				AND CT.CUSTOMER_TRX_ID =
                                                   RECEIPT.APPLIED_CUSTOMER_TRX_ID(+)
				AND CT.CUSTOMER_TRX_ID =
                                                   REFUND.CUSTOMER_TRX_ID(+)
				AND CT.CUSTOMER_TRX_ID =
                                                   CM_INV.CUSTOMER_TRX_ID(+)
				AND CT.BATCH_SOURCE_ID =
                                                   SR.BATCH_SOURCE_ID
				AND CT.ORG_ID = SR.ORG_ID
				AND ( DIST.ACCTD_AMOUNT
                                                   - ABS (NVL (CM_AMOUNT,
				0)))
                                                - NVL (RCT_AMOUNT,
				0)
                                                + NVL (RFN_AMOUNT,
				0)
                                                + NVL (CMINV_AMOUNT,
				0) <> 0
				AND CT.ORG_ID IN (222, 522)
				AND TRUNC (DIST.GL_DATE) <=
                                                   TO_DATE (:P_END_DATE,
				'DD-MON-RRRR'))
		GROUP BY
			SALES_CHANNEL_CODE,
			AREA,
			CUSTOMER_ID,
			CUSTOMER_NUMBER,
			CUSTOMER_NAME,
			DAY_COUNT
	UNION ALL
		SELECT
			SALES_CHANNEL_CODE,
			AREA,
			CUSTOMER_ID,
			CUSTOMER_NUMBER,
			CUSTOMER_NAME,
			(CASE
				WHEN DAY_COUNT < 90
                                        THEN
                                           SUM (BALANCE_DUE)
				ELSE
                                           0
			END)
                                       DAYS_90,
			(CASE
				WHEN DAY_COUNT > 90
					AND DAY_COUNT < 181
                                        THEN
                                           SUM (BALANCE_DUE)
					ELSE
                                           0
				END)
                                       DAYS_180,
			(CASE
				WHEN DAY_COUNT > 180
					AND DAY_COUNT < 271
                                        THEN
                                           SUM (BALANCE_DUE)
					ELSE
                                           0
				END)
                                       DAYS_270,
			(CASE
				WHEN DAY_COUNT > 270
					AND DAY_COUNT <= 365
                                        THEN
                                           SUM (BALANCE_DUE)
					ELSE
                                           0
				END)
                                       DAYS_360,
			(CASE
				WHEN DAY_COUNT > 365
                                        THEN
                                           SUM (BALANCE_DUE)
				ELSE
                                           0
			END)
                                       PLUS_DAYS_360,
			SUM (BALANCE_DUE)
		FROM
			(
			SELECT
				CUST.CUSTOMER_ID,
				CUST.CUSTOMER_NUMBER,
				CUST.SALES_CHANNEL_CODE,
				CUST.AREA,
				CUST.CUSTOMER_NAME,
				ACRA.CASH_RECEIPT_ID,
				ACRA.RECEIPT_NUMBER,
				ACRA.DOC_SEQUENCE_VALUE,
				( (TO_DATE (:P_END_DATE,
				'DD-MON-RRRR'))
                                               - APSA.GL_DATE)
                                                 DAY_COUNT,
				ACRA.AMOUNT,
				APSA.GL_DATE,
				GCC.SEGMENT5
                                              || '-'
                                              || VL2.DESCRIPTION
                                                 UNAPP_GCC,
				( SUM (
                                                      ARAA.AMOUNT_APPLIED
                                                    * NVL (ACRA.EXCHANGE_RATE,
				1))
                                               * (-1))
                                                 BALANCE_DUE
			FROM
				APPS.AR_CASH_RECEIPTS_ALL ACRA,
				APPS.HR_OPERATING_UNITS OU,
				APPS.AR_RECEIPT_METHOD_ACCOUNTS_ALL ARMA,
				APPS.AR_RECEIVABLE_APPLICATIONS_ALL ARAA,
				APPS.AR_PAYMENT_SCHEDULES_ALL APSA,
				APPS.GL_CODE_COMBINATIONS GCC,
				APPS.FND_FLEX_VALUES_VL VL2,
				APPS.SOFTLN_AR_CUSTOMERS_ALL_V CUST
			WHERE
				ACRA.REMIT_BANK_ACCT_USE_ID =
                                                     ARMA.REMIT_BANK_ACCT_USE_ID
				AND ARAA.CODE_COMBINATION_ID =
                                                     ARMA.UNAPPLIED_CCID
				AND ACRA.CASH_RECEIPT_ID =
                                                     ARAA.CASH_RECEIPT_ID
				AND ACRA.CASH_RECEIPT_ID =
                                                     APSA.CASH_RECEIPT_ID
				AND ACRA.RECEIPT_METHOD_ID =
                                                     ARMA.RECEIPT_METHOD_ID
				AND GCC.CODE_COMBINATION_ID =
                                                     ARMA.UNAPPLIED_CCID
				AND ACRA.ORG_ID = OU.ORGANIZATION_ID
				--AND OU.SET_OF_BOOKS_ID = 2043
				--AND ( :P_LEDGER IS NULL OR OU.SET_OF_BOOKS_ID  = :P_LEDGER)
				AND VL2.FLEX_VALUE = GCC.SEGMENT5
				AND OU.ORGANIZATION_ID IN (222, 522)
					AND VL2.FLEX_VALUE_SET_ID = 1016488
					AND ACRA.PAY_FROM_CUSTOMER =
                                                     CUST.CUSTOMER_ID
					AND TRUNC (APSA.GL_DATE) <
                                                       TO_DATE (:P_END_DATE,
					'DD-MON-RRRR')
                                                     + 1
						AND TRUNC (ARAA.GL_DATE) <
                                                       TO_DATE (:P_END_DATE,
						'DD-MON-RRRR')
                                                     + 1
							AND (
							SELECT
								B.STATUS
							FROM
								APPS.AR_CASH_RECEIPT_HISTORY_ALL B
							WHERE
								ACRA.CASH_RECEIPT_ID =
                                                                 B.CASH_RECEIPT_ID
								AND B.CURRENT_RECORD_FLAG =
                                                                 'Y') = 'CLEARED'
						GROUP BY
							CUST.CUSTOMER_ID,
							CUST.CUSTOMER_NUMBER,
							CUST.SALES_CHANNEL_CODE,
							CUST.AREA,
							CUST.CUSTOMER_NAME,
							ACRA.CASH_RECEIPT_ID,
							ACRA.RECEIPT_NUMBER,
							ACRA.DOC_SEQUENCE_VALUE,
							GCC.SEGMENT5
                                              || '-'
                                              || VL2.DESCRIPTION,
							ACRA.AMOUNT,
							APSA.GL_DATE
						HAVING
							SUM (ARAA.AMOUNT_APPLIED) <> 0)
		GROUP BY
			SALES_CHANNEL_CODE,
			AREA,
			CUSTOMER_ID,
			CUSTOMER_NUMBER,
			CUSTOMER_NAME,
			DAY_COUNT)
	WHERE
		1 = 1
		-- AND(:P_DEALER IS NULL  OR SALES_CHANNEL_CODE = :P_DEALER)
		AND('CORPORATE WITP' IS NULL
			OR SALES_CHANNEL_CODE = 'CORPORATE WITP')
	GROUP BY
		CUSTOMER_ID,
		CUSTOMER_NUMBER,
		SALES_CHANNEL_CODE,
		AREA,
		CUSTOMER_NAME
                ),
	TRANSACTIONS
             AS (
	SELECT
		CUSTOMER_ID,
		GL_DATE,
		TRX_TYPE,
		NVL (DR_AMOUNT,
		0) DR_AMOUNT,
		NVL (CR_AMOUNT,
		0) CR_AMOUNT,
		(NVL (DR_AMOUNT,
		0) - NVL (CR_AMOUNT,
		0)) AMOUNT
	FROM
		APPS.XX_AR_CUSTOMER_DTL_LEDGER DL
	WHERE
		GL_DATE <= :P_END_DATE
		AND ORG_ID IN (222, 522)
                ),
             OPENING_BALANCE
             AS (
	SELECT
		CUSTOMER_ID,
		NVL (SUM (AMOUNT),
		0) OPENING_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		GL_DATE < :P_START_DATE
	GROUP BY
		CUSTOMER_ID),
	SALES
             AS (
	SELECT
		CUSTOMER_ID,
		NVL (SUM (DR_AMOUNT),
		0) SALES_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		UPPER (TRX_TYPE) IN ('GO-LIVE OPENING BALANCE',
                                                   'SALES')
			AND GL_DATE BETWEEN :P_START_DATE AND :P_END_DATE
		GROUP BY
			CUSTOMER_ID),
	RETURNS
             AS (
	SELECT
		CUSTOMER_ID,
		NVL (SUM (CR_AMOUNT),
		0) RETURN_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		UPPER (TRX_TYPE) = 'RETURN'
			AND GL_DATE BETWEEN :P_START_DATE AND :P_END_DATE
		GROUP BY
			CUSTOMER_ID),
	DEBIT
             AS (
	SELECT
		CUSTOMER_ID,
		NVL (SUM (DR_AMOUNT),
		0) DEBIT_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		UPPER (TRX_TYPE) = 'DEBIT ADJUSTMENT'
			AND GL_DATE BETWEEN :P_START_DATE AND :P_END_DATE
		GROUP BY
			CUSTOMER_ID),
	CREDIT
             AS (
	SELECT
		CUSTOMER_ID,
		NVL (SUM (CR_AMOUNT),
		0) CREDIT_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		UPPER (TRX_TYPE) = 'CREDIT ADJUSTMENT'
			AND GL_DATE BETWEEN :P_START_DATE AND :P_END_DATE
		GROUP BY
			CUSTOMER_ID),
	REFUNDS
             AS (
	SELECT
		CUSTOMER_ID,
		NVL (SUM (DR_AMOUNT),
		0) REFUND_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		UPPER (TRX_TYPE) = 'CUSTOMER REFUND'
			AND GL_DATE BETWEEN :P_START_DATE AND :P_END_DATE
		GROUP BY
			CUSTOMER_ID),
	RECEIPTS
             AS (
	SELECT
		CUSTOMER_ID,
		NVL (SUM (CR_AMOUNT),
		0) RECEIPT_AMOUNT
	FROM
		TRANSACTIONS
	WHERE
		UPPER (TRX_TYPE) = 'RECEIPTS'
			AND GL_DATE BETWEEN :P_START_DATE AND :P_END_DATE
		GROUP BY
			CUSTOMER_ID)
	SELECT
		CZ.*,
		NVL (OPENING_AMOUNT,
		0) OPENING_BALANCE,
		NVL (SALES_AMOUNT,
		0) SALES_AMOUNT,
		NVL (DEBIT_AMOUNT,
		0) + NVL (REFUND_AMOUNT,
		0) DEBIT_AMOUNT,
		NVL (CREDIT_AMOUNT,
		0) CREDIT_AMOUNT,
		NVL (RECEIPT_AMOUNT,
		0) CLEARED_RECEIPT,
		NVL (RETURN_AMOUNT,
		0) SALES_RETURN,
		( ( NVL (OPENING_AMOUNT,
		0)
                   + NVL (SALES_AMOUNT,
		0)
                   + NVL (DEBIT_AMOUNT,
		0)
                   + NVL (REFUND_AMOUNT,
		0))
                - ( NVL (CREDIT_AMOUNT,
		0)
                   + NVL (RECEIPT_AMOUNT,
		0)
                   + NVL (RETURN_AMOUNT,
		0)))
                  CLOSING_BALANCE
	FROM
		CUSTOMER_ZONE CZ,
		OPENING_BALANCE OB,
		SALES S,
		RETURNS R,
		DEBIT D,
		CREDIT C,
		REFUNDS FN,
		RECEIPTS RCT
	WHERE
		CZ.CUSTOMER_ID = OB.CUSTOMER_ID(+)
		AND CZ.CUSTOMER_ID = S.CUSTOMER_ID(+)
		AND CZ.CUSTOMER_ID = R.CUSTOMER_ID(+)
		AND CZ.CUSTOMER_ID = D.CUSTOMER_ID(+)
		AND CZ.CUSTOMER_ID = C.CUSTOMER_ID(+)
		AND CZ.CUSTOMER_ID = FN.CUSTOMER_ID(+)
		AND CZ.CUSTOMER_ID = RCT.CUSTOMER_ID(+)
		AND ( OPENING_AMOUNT <> 0
			OR NVL (SALES_AMOUNT,
			0) <> 0
				OR NVL (DEBIT_AMOUNT,
				0) <> 0
					OR NVL (CREDIT_AMOUNT,
					0) <> 0
						OR NVL (RECEIPT_AMOUNT,
						0) <> 0
							OR NVL (RETURN_AMOUNT,
							0) <> 0
								OR NVL (REFUND_AMOUNT,
								0) <> 0)
                                                   )
WHERE
	WITP_CODE = :WITP_CODE
"""

party_default_addr_sql = """
SELECT
	DISTINCT PARTY.PARTY_ID,
	PARTY.PARTY_NUMBER,
	PARTY.PARTY_NAME,
	CUST_ACCT.ACCOUNT_NUMBER AS WITP_CODE,
	LOC.ADDRESS1 AS ADDRESS
FROM
	APPS.HZ_PARTIES PARTY,
	APPS.HZ_CUST_ACCOUNTS CUST_ACCT,
	APPS.HZ_CUST_SITE_USES_ALL SITE_USE,
	APPS.HZ_CUST_ACCT_SITES_ALL ACCT_USE,
	APPS.HZ_PARTY_SITES PS,
	APPS.HZ_LOCATIONS LOC,
	APPS.SOFTLN_AR_CUSTOMERS_ALL_V CUST,
	apps.ZX_PARTY_TAX_PROFILE TP,
	APPS.HZ_CUST_PROFILE_AMTS HCPA,
	APPS.SOFTLN_AR_CONTACTS_PHONE_V ACP
WHERE
	PARTY.PARTY_ID = CUST_ACCT.PARTY_ID
	AND PARTY.PARTY_ID = CUST.PARTY_ID
	AND PARTY.PARTY_ID = TP.PARTY_ID
	AND CUST_ACCT.cust_account_id = HCPA.cust_account_id(+)
	AND SITE_USE.CUST_ACCT_SITE_ID = ACCT_USE.CUST_ACCT_SITE_ID
	AND CUST_ACCT.CUST_ACCOUNT_ID = ACCT_USE.CUST_ACCOUNT_ID
	AND ACCT_USE.PARTY_SITE_ID = PS.PARTY_SITE_ID
	AND PS.LOCATION_ID = LOC.LOCATION_ID
	AND ACP.CUSTOMER_ID(+) = CUST.CUSTOMER_ID
	AND CUST_ACCT.ACCOUNT_NUMBER = :witp_code
	AND SITE_USE.SITE_USE_CODE = 'SHIP_TO'
	AND SITE_USE.LOCATION = 'Witp'
	AND PARTY.STATUS = 'A'
	AND CUST_ACCT.STATUS = 'A'
	AND SITE_USE.STATUS = 'A'
	AND ACCT_USE.STATUS = 'A'
"""

party_collections_sql = """
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
       TR.TOTAL_RECIPT_AMOUNT AS TOTAL_RECEIPT_AMOUNT
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


party_addresses_sql = """
WITH DEFAULT_ADDRESS
     AS (  SELECT PARTY_ID,
                  ACCOUNT_NUMBER,
                  ORG_ID,
                  ADDRESS
             FROM (SELECT DISTINCT PARTY.PARTY_ID,
                                   CUST_ACCT.ACCOUNT_NUMBER,
                                   SITE_USE.ORG_ID,
                                   LOC.ADDRESS1 AS ADDRESS,
                                   SITE_USE.SITE_USE_CODE
                     FROM APPS.HZ_PARTIES PARTY,
                          APPS.HZ_CUST_ACCOUNTS CUST_ACCT,
                          APPS.HZ_CUST_SITE_USES_ALL SITE_USE,
                          APPS.HZ_CUST_ACCT_SITES_ALL ACCT_USE,
                          APPS.HZ_PARTY_SITES PS,
                          APPS.HZ_LOCATIONS LOC,
                          APPS.SOFTLN_AR_CUSTOMERS_ALL_V CUST,
                          apps.ZX_PARTY_TAX_PROFILE TP,
                          APPS.HZ_CUST_PROFILE_AMTS HCPA,
                          APPS.SOFTLN_AR_CONTACTS_PHONE_V ACP
                    WHERE     PARTY.PARTY_ID = CUST_ACCT.PARTY_ID
                          AND PARTY.PARTY_ID = CUST.PARTY_ID
                          AND PARTY.PARTY_ID = TP.PARTY_ID
                          AND CUST_ACCT.cust_account_id =
                                 HCPA.cust_account_id(+)
                          AND SITE_USE.CUST_ACCT_SITE_ID =
                                 ACCT_USE.CUST_ACCT_SITE_ID
                          AND CUST_ACCT.CUST_ACCOUNT_ID =
                                 ACCT_USE.CUST_ACCOUNT_ID
                          AND ACCT_USE.PARTY_SITE_ID = PS.PARTY_SITE_ID
                          AND PS.LOCATION_ID = LOC.LOCATION_ID
                          AND ACP.CUSTOMER_ID(+) = CUST.CUSTOMER_ID
                          AND CUST_ACCT.ACCOUNT_NUMBER = :witp_code
                          AND PARTY.STATUS = 'A'
                          AND CUST_ACCT.STATUS = 'A'
                          AND SITE_USE.STATUS = 'A'
                          AND ACCT_USE.STATUS = 'A'
                          AND SITE_USE.PRIMARY_FLAG = 'Y')
         GROUP BY PARTY_ID,
                  ACCOUNT_NUMBER,
                  ORG_ID,
                  ADDRESS),
     ALL_ADDRESS
     AS (  SELECT PARTY_ID,
                  ACCOUNT_NUMBER,
                  ORG_ID,
                  ADDRESS,
                  LOCATION,
                  PH_ADDRESS
             FROM (SELECT DISTINCT PARTY.PARTY_ID,
                                   CUST_ACCT.ACCOUNT_NUMBER,
                                   SITE_USE.ORG_ID,
                                   LOC.ADDRESS1 AS ADDRESS,
                                   SITE_USE.SITE_USE_CODE,
                                   SITE_USE.LOCATION,
                                   LOC.ADDRESS_LINES_PHONETIC PH_ADDRESS
                     FROM APPS.HZ_PARTIES PARTY,
                          APPS.HZ_CUST_ACCOUNTS CUST_ACCT,
                          APPS.HZ_CUST_SITE_USES_ALL SITE_USE,
                          APPS.HZ_CUST_ACCT_SITES_ALL ACCT_USE,
                          APPS.HZ_PARTY_SITES PS,
                          APPS.HZ_LOCATIONS LOC,
                          APPS.SOFTLN_AR_CUSTOMERS_ALL_V CUST,
                          APPS.ZX_PARTY_TAX_PROFILE TP,
                          APPS.HZ_CUST_PROFILE_AMTS HCPA,
                          APPS.SOFTLN_AR_CONTACTS_PHONE_V ACP
                    WHERE     PARTY.PARTY_ID = CUST_ACCT.PARTY_ID
                          AND PARTY.PARTY_ID = CUST.PARTY_ID
                          AND PARTY.PARTY_ID = TP.PARTY_ID
                          AND CUST_ACCT.cust_account_id =
                                 HCPA.cust_account_id(+)
                          AND SITE_USE.CUST_ACCT_SITE_ID =
                                 ACCT_USE.CUST_ACCT_SITE_ID
                          AND CUST_ACCT.CUST_ACCOUNT_ID =
                                 ACCT_USE.CUST_ACCOUNT_ID
                          AND ACCT_USE.PARTY_SITE_ID = PS.PARTY_SITE_ID
                          AND PS.LOCATION_ID = LOC.LOCATION_ID
                          AND ACP.CUSTOMER_ID(+) = CUST.CUSTOMER_ID
                          AND CUST_ACCT.ACCOUNT_NUMBER = :witp_code
                          AND PARTY.STATUS = 'A'
                          AND CUST_ACCT.STATUS = 'A'
                          AND SITE_USE.STATUS = 'A'
                          AND ACCT_USE.STATUS = 'A'
                          AND SITE_USE.PRIMARY_FLAG <> 'Y')
         GROUP BY PARTY_ID,
                  ACCOUNT_NUMBER,
                  ORG_ID,
                  ADDRESS,
                  LOCATION,
                  PH_ADDRESS)
SELECT DISTINCT A.PARTY_ID,
       HP.PARTY_NAME,
       A.ACCOUNT_NUMBER WITP_CODE,
       A.ORG_ID,
       D.ADDRESS DEFAULT_ADDRESS,
       A.ADDRESS ALL_ADDRESS,
       LOCATION CONTACT_PERSON,
       PH_ADDRESS MOBILE_NUMBER
  FROM DEFAULT_ADDRESS D, ALL_ADDRESS A, HZ_PARTIES HP
 WHERE D.PARTY_ID = A.PARTY_ID AND D.PARTY_ID = HP.PARTY_ID
"""
