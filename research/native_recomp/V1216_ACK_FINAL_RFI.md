# V1216: final cleared-PI interrupt return

Create a distinct epilogue witness for the third saved frame after ACK; the earlier pending-SI epilogue cannot be recycled. Verify dispatcher enable/reschedule/loader sequence, restored integer/GQR state and both native RFI polls without another interrupt. Eight positive and twelve negative synthetic cases; CI pending.
