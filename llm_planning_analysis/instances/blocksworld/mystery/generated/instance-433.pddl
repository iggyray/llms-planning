(define (problem BW-generalization-4)
(:domain mystery-4ops)(:objects h i b j k e f l c g a)
(:init 
(harmony)
(planet h)
(planet i)
(planet b)
(planet j)
(planet k)
(planet e)
(planet f)
(planet l)
(planet c)
(planet g)
(planet a)
(province h)
(province i)
(province b)
(province j)
(province k)
(province e)
(province f)
(province l)
(province c)
(province g)
(province a)
)
(:goal
(and
(craves h i)
(craves i b)
(craves b j)
(craves j k)
(craves k e)
(craves e f)
(craves f l)
(craves l c)
(craves c g)
(craves g a)
)))