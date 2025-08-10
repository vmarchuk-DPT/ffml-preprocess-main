from log_config.log_config import logger


def is_evil(result):

	# Only evaluate bipartite questions.
	print('*********************')
	print(f'here is question type = {result.question.type }')
	print(f'here is path = {len(result.path)}')
	#print(f"here is heuristic for straight line = {result.features['diverge']['maxDivergence'][0]}")
	print(f'here is duration = {result.question.duration}')
	if result.question.type != 'bipartite_choice' and result.question.type != 'tripartite_choice':
		print(f'bad - not bipartite or tripartite. question_type = {result.question.type}')
		logger.debug(f'Result not sent to database: not a bipartite choice, {result.participant}, {result.question.stimulus}')
		return True

	# Only evaluate mouse paths (not touchscreens).
	#if len(result.path) <= 10:
	#	print('bad - result.path <=10')
#		logger.debug(f'Result not sent to database: short path {result.participant}, {result.question.stimulus}')
		#return True

	# Heuristic for straight line.
	#if result.features['diverge']['maxDivergence'][0] < 0.1:
#		print('bad diverge max divergence[0] < 0.1 ')
#		logger.debug(f'Result not sent to database: straight line, {result.participant}, {result.question.stimulus}')
#		return True

	#if result.question.duration > 2000:
	#if result.question.duration < 6000:  # <= чтоб отфильтровать всех остальных
	#	print('bad result.question.duration > 6000')
#		logger.debug(f'Result not sent to database: question duration too great {result.participant}, {result.question.stimulus}')
#		return True

	print('ITES OK')
	return False
