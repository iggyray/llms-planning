(define (problem BW-generalization-4)
(:domain blocksworld-4ops)(:objects l d k e c j i g f)
(:init 
(handempty)
(ontable l)
(ontable d)
(ontable k)
(ontable e)
(ontable c)
(ontable j)
(ontable i)
(ontable g)
(ontable f)
(clear l)
(clear d)
(clear k)
(clear e)
(clear c)
(clear j)
(clear i)
(clear g)
(clear f)
)
(:goal
(and
(on l d)
(on d k)
(on k e)
(on e c)
(on c j)
(on j i)
(on i g)
(on g f)
)))